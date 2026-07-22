# 가변 휠 제어 시스템

이 문서는 프로젝트에서 **무엇을 개발하는지와 현재 작업·구현 현황**을 설명한다. 세부 작업 순서와 단계별 진행도는 [TODO_LIST.md](TODO_LIST.md), 작업자의 행동 지침은 [AGENTS.md](AGENTS.md)를 따른다.

## 1. 프로젝트 개요

이 프로젝트는 PC 제어 시스템에서 로봇 보드로 명령을 전송하여, 로봇에 장착되는 2개 이상의 **가변 휠**을 조작하기 위한 소프트웨어 기반을 구축한다. 이 프로젝트에서는 기존에 Mecanum wheel로 표현한 가변형 바퀴를 `가변 휠`로 통일해 부른다.

각 가변 휠에는 다음 두 모터가 들어갈 예정이다.

- **주행 모터(`drive_motor`)**: 바퀴 전체를 회전시켜 로봇을 이동시킨다.
- **조절 모터(`adjustment_motor`)**: 와이어를 당기거나 풀어 작업 공간에 맞게 바퀴 크기를 조절한다. 이 모터에는 encoder를 부착한다.

최종적으로는 사용자의 이동 입력을 각 가변 휠의 회전 방향과 속도로 변환해 전후·상하·좌우 이동을 제어한다. PC가 보내는 하나의 로봇 제어 명령에는 등록된 모든 가변 휠의 주행 모터 제어값과 조절 모터 제어값이 함께 들어간다. 다만 실제 이동 자유도와 wheel mixing 식은 가변 휠 수, 장착 방향, passive roller 각도 및 접촉 조건이 확정된 후 실험으로 검증해야 한다.

## 2. 현재 상태와 이번 단계의 범위

현재 로봇 하드웨어는 아직 만들어지지 않았다. 소프트웨어는 단일 가변 휠 시험 UI의 prototype으로 네 개의 토글, 독립 UI 상태 model과 감김 위치 simulation까지 구현된 상태다. motor·encoder·robot board 및 protocol에는 아직 연결되지 않았다.

### 현재 구현 상태

Python 3.12와 표준 `tkinter`를 이용한 기본 UI가 구현되어 있다. project root의 `app.py`가 실행 진입점이며, 상태 계산은 `src/ui/models.py`, 공용 widget은 `src/ui/widgets.py`, 화면 구성과 interaction은 `src/ui/control_panel.py`에서 불러온다. 모든 import와 문서 경로는 project root 기준 상대 구조를 사용하며 특정 PC의 사용자 폴더에 의존하지 않는다. `run_ui.py`는 기존 실행 명령과의 호환을 위한 launcher다.

- 주행 모터 `OFF/ON` 토글
- 주행 모터 `+/-` 방향 토글 (`+`는 전진, `-`는 후진)
- 조절 모터 `OFF/ON` 토글
- 조절 모터 감기/풀기 토글
- 0~10 눈금의 감김 위치 gauge와 0.5~9.5 이동 제한
- 현재 위치(파란색 짧은 선과 아래쪽 `▲`), 목표(빨간색 짧은 선과 위쪽 `▼`), 목표 도달(보라색) 표시
- mouse를 누른 채 좌우로 움직이는 목표 미리보기와 button을 놓을 때 목표를 확정하는 drag 조작
- 목표 이동 중 `멈춤`으로 전환되는 `이동` button과 현재 위치로 목표를 되돌리는 `초기화` button
- `◀ 현재속도 ▶` 형태의 0.1~1.0 감김 simulation 속도 조절(0.1 단위)
- 네 토글을 하나로 묶은 `WheelUiState`
- 감김 위치와 목표를 분리한 `WindingGaugeState`
- 향후 application service가 상태 변경을 받을 수 있는 callback 경계

네 토글은 모두 시작할 때 왼쪽 항목이 선택된다. 기본값은 주행 모터 `OFF`, 주행 방향 `+`, 조절 모터 `OFF`, 와이어 방향 `풀기`다. 화면에는 현재가 `하드웨어 미연결` 상태임을 표시한다.

현재 감김 위치는 encoder 측정값이 아닌 UI 내부 simulation 값이다. 조절 모터를 `ON`으로 바꾸면 감기/풀기 방향에 따라 선택 속도로 이동한다. gauge에서 mouse를 누른 채 움직이면 빨간 목표가 따라오고, 놓는 순간 목표가 확정된다. `이동`을 누르면 목표 방향을 자동 선택하고 button은 `멈춤`으로 바뀐다. `멈춤`을 누르면 조절 모터가 `OFF`가 되어 현재 위치에서 정지하고 button은 다시 `이동`으로 돌아오며, 같은 목표를 향해 다시 이동할 수 있다. 목표 도달 시에도 자동 정지하며, `초기화`는 목표를 현재 위치로 되돌린다. 실제 motor 제어 명령, encoder 원시값과 보정 위치, 주행 속도 수치 입력, 통신과 board 연동은 아직 구현되지 않았다.

### 첫 구현 목표: 단일 가변 휠 제어 모듈

첫 개발 milestone의 목표는 제어 PC의 UI에서 가변 휠 하나를 선택해 두 모터를 제어하고 조절 모터의 위치 추정 상태를 확인하는 것이다. 핵심 제어 모듈은 `VariableWheelController`라는 내부 이름을 기준으로 계획하며 다음 책임만 가진다.

- 제어할 가변 휠 하나의 `wheel_id`를 가진다.
- 주행 모터와 조절 모터의 제어 입력을 함께 받는다.
- 두 모터 입력을 각각 검증한다.
- 검증된 값을 하나의 `WheelControlCommand`로 생성한다.
- 상위 계층이 같은 module interface로 여러 가변 휠을 구성할 수 있게 한다.

단일 가변 휠 시험용 UI는 application service를 통해 다음 기능을 제공한다.

- 주행 모터 회전 방향 선택
- 주행 모터 목표 속도 입력과 정지
- 조절 모터 감기·풀기 또는 목표 위치 제어
- encoder 원시값과 영점 기준 현재 위치 표시
- 추정 가능한 경우 와이어 감김량과 가변 휠 크기 표시
- 위치 추정의 정상·미보정·오류 상태 표시

UI는 `VariableWheelController`, protocol 또는 transport의 내부 구현을 직접 소유하지 않는다. 첫 software prototype은 가변 휠 하나만 등록한 test 설정, mock board와 encoder telemetry로 전체 흐름을 시험한다. 실제 motor와 robot board 연동은 hardware 사양과 안전값이 확정된 뒤 검증한다. 이후 이 단일 가변 휠 module을 여러 개 사용해 `RobotControlCommand`를 조립한다.

### 이번 단계에 포함되는 범위

- PC 제어 프로그램의 기본 구조 설계
- 전송 방식과 분리된 명령·응답 모델 설계
- ASCII 기반 초기 protocol 설계
- 모든 가변 휠의 두 모터 제어값을 포함하는 통합 명령 생성·검증 설계
- PC에서 통합 명령 하나를 로봇 보드까지 보내는 흐름 설계
- encoder telemetry를 이용한 크기 조절 상태 감시 및 과인장 방지 로직 설계
- 단일 가변 휠 시험용 UI에서 두 모터 제어와 위치 추정 상태 확인
- 하드웨어 없이 개발할 수 있는 mock transport와 board simulator 계획
- 향후 다중 wheel 제어를 수용할 수 있는 식별자와 명령 구조 설계

### 이번 단계에 포함되지 않는 범위

- 로봇 보드가 명령을 각 가변 휠 controller로 재분배하는 firmware 구현
- 모터 driver 및 encoder hardware의 실제 구동
- 실제 로봇의 Mecanum kinematics 보정
- 여러 가변 휠을 동시에 조작하는 최종 통합 UI

현재는 단일 가변 휠 module을 검증하는 최소 UI를 구현 대상으로 삼는다. 여러 가변 휠의 이동 명령을 동시에 조작하는 최종 통합 UI는 향후 단계로 둔다.

## 3. 시스템 경계

```text
[사용자 / 단일 가변 휠 시험 UI]
        |
        v
[PC Application]
  - 사용자 명령 해석
  - 이동 명령 조정
  - 크기 목표 및 안전 상태 감시
  - 모든 가변 휠 제어값을 하나의 명령으로 조립
        |
        v
[Protocol Codec]
  - 명령 객체 <-> ASCII frame
        |
        v
[Transport Adapter]
  - Serial/TCP 등 교체 가능한 연결
        |
        v
[Robot Board]
  - 현재 단계: 통합 로봇 제어 명령 수신 지점
  - 향후 단계: 가변 휠별 명령 재분배 및 실시간 안전 제어
        |
        v
[가변 휠 1..N]
  - 주행 모터
  - 조절 모터 + encoder
```

PC 프로그램은 특정 통신 장치에 직접 의존하지 않는다. 명령 의미를 표현하는 domain model, ASCII frame을 처리하는 protocol codec, 실제 입출력을 담당하는 transport adapter를 분리한다. 따라서 이후 Serial, USB, TCP 또는 다른 binary protocol로 바뀌더라도 상위 제어 로직을 최대한 유지할 수 있어야 한다.

## 4. 제안 소프트웨어 구조

아래 구조 중 `app.py`, `src/ui/`, `run_ui.py`, `tests/test_ui_state.py`와 `tests/test_launcher.py`만 현재 구현되어 있으며 나머지는 계획안이다.

```text
app.py                 # project root의 UI 실행 진입점
run_ui.py              # 기존 실행 명령 호환 launcher
src/
  application/       # 제어 use case와 명령 실행 흐름
  domain/            # Wheel ID, 명령, 상태, 오류 등 통신 독립 모델
  wheel/             # 단일 가변 휠의 두 모터 제어 module
  motion/            # 이동 입력과 가변 휠별 속도 명령의 변환
  safety/            # encoder limit, timeout, fault, emergency stop 정책
  protocol/          # ASCII encoder/decoder 및 frame 검증
  transport/         # Serial/TCP/mock 연결 adapter
  telemetry/         # ACK, 상태 및 encoder feedback 처리
  ui/
    models.py        # UI 상태, 범위와 시간 기반 위치 simulation
    widgets.py       # 토글과 감김 gauge widget
    control_panel.py # 단일 휠 화면 조립과 interaction
  config/            # wheel 수, 제한값, 통신 설정
  cli/               # 초기 시험용 명령 인터페이스
tests/
  test_ui_state.py   # 현재 구현된 UI 상태 model 단위 시험
  test_launcher.py   # 현재 폴더와 무관한 launcher import 시험
  unit/              # 향후 domain, protocol, safety 단위 시험
  integration/       # 향후 mock board 송수신 시험
```

### 현재 UI 실행

추가 package 설치는 필요하지 않다. project 폴더를 다른 위치나 PC로 복사한 뒤 해당 project root에서 다음과 같이 실행한다.

```powershell
python app.py
```

기존 launcher도 같은 project root에서 사용할 수 있다.

```powershell
python run_ui.py
```

IDE에서는 project root의 `app.py`를 실행 파일로 선택한다.

```powershell
python app.py
```

UI 창을 열지 않고 import 상태만 확인할 수도 있다.

```powershell
python app.py --check
```

단위 test는 다음과 같이 실행한다.

```powershell
python -m unittest discover -s tests -v
```

### GitHub 연동 상태

- local Git branch: `main`
- remote 이름: `origin`
- remote 저장소: `https://github.com/whgms259/Soft_robot.git`
- Python cache, 가상환경, IDE 설정과 test 산출물은 `.gitignore`에서 제외한다.
- GitHub 일반 파일 크기 제한을 초과한 약 134.9MB의 kickoff PDF는 사용자 요청에 따라 project에서 삭제했다.
- 원격 저장소는 연결 시점에 commit이 없는 빈 저장소로 확인했다.
- Git commit 작성자 이름과 email이 설정되지 않아 initial commit과 push는 아직 수행하지 않았다.

### UI 구현 중 수정된 문제

- 원인: 최초 기본 창 높이 410px가 UI 요구 높이 458px보다 작아 일부 화면이 잘릴 가능성이 있었다.
- 해결: 최초 토글 UI는 기본 창을 660×500px로 조정했고, gauge와 속도 control 추가 후에는 기본·최소 창 높이를 760px로 확장했다. 현재 UI 요구 크기는 Windows 환경에서 592×746px로 확인했다.
- 남은 제한: 현재 검증은 Windows의 `tkinter 8.6` 환경에서 수행했으며 다른 OS의 글꼴과 배치는 추가 확인이 필요하다.

### UI 실행 오류 수정 기록

- 증상: refactoring 직후 하위 `src/ui/app.py`를 직접 실행하면 package 상대 import 오류가 발생했다.
- 원인: package 내부 파일을 단독 실행하면 상위 package 정보가 없어 상대 import를 해석할 수 없다.
- 해결: 실행 진입점 `app.py`를 project root로 이동하고 내부 구현만 `src/ui/` package에 남겼다.
- 검증: 임시 폴더에 `app.py`, `run_ui.py`, `src/`를 복사한 후 복사본의 `python app.py --check`를 실행했다.
- 남은 제한: project 내부의 파일·폴더 상대 구조는 유지해야 하며 `src/ui/` 내부 module만 따로 복사해서는 실행할 수 없다.

- 증상: `ModuleNotFoundError: No module named 'src'`
- 원인: 과거 package module 실행 방식은 현재 작업 폴더에 따라 `src` 검색 경로가 달라졌다.
- 해결: project root의 `app.py`를 기본 실행점으로 정하고 `run_ui.py`도 같은 root module을 불러오도록 변경했다.
- 검증: project를 임시 위치로 복사하고 복사된 root 진입점의 import 검사를 수행했다.
- 남은 제한: 상대 명령 `python app.py`를 사용할 때는 project root를 현재 작업 폴더로 두어야 한다.

## 5. 핵심 모델과 책임

### 가변 휠 식별자

모든 가변 휠은 고유한 `wheel_id`를 가진다. 가변 휠 번호는 설정에 등록하며, 명령 안에서 어떤 두 모터 제어값이 어느 가변 휠에 속하는지 구분하는 기준으로 사용한다.

### 가변 휠 제어 명령(Wheel control command)

`WheelControlCommand` 하나는 가변 휠 한 개의 두 모터 제어값을 묶는다.

- 대상 `wheel_id`
- 주행 모터의 부호가 있는 목표 속도 또는 정규화된 출력값
- 조절 모터의 목표 encoder position 또는 목표 가변 휠 크기
- 조절 모터의 허용 속도와 안전 제한에 필요한 값

속도의 실제 단위(RPM, rad/s 또는 정규화 값)는 motor/driver 사양 확정 후 결정한다. 조절 모터의 제어값을 변경하지 않을 때 사용할 유지 또는 무동작 표현도 ASCII protocol V1 확정 전에 정의해야 한다.

첫 구현의 `VariableWheelController`는 이 명령을 생성하는 단일 가변 휠 module이다. 이 module은 통신, 전체 로봇 명령 조립 및 board 내부 명령 분배를 담당하지 않는다.

### Encoder 기반 위치 추정

조절 모터의 현재 위치는 `WheelPositionEstimator`가 담당한다. 위치 추정은 다음 정보를 단계적으로 계산하거나 표시한다.

1. encoder에서 수신한 원시 count
2. 기준 영점으로부터의 상대 encoder position
3. encoder resolution과 gear ratio를 적용한 조절 모터 또는 spool 회전량
4. spool의 유효 반경을 적용한 와이어 감김·풀림 길이
5. calibration 관계를 적용한 가변 휠 크기 추정값

각 결과에는 정상 여부와 기준 시각을 함께 관리한다. encoder telemetry가 없거나 오래됐거나 영점·calibration이 완료되지 않았으면 UI는 정확한 가변 휠 크기로 표시하지 않고 `미보정` 또는 `유효하지 않음` 상태를 보여야 한다.

와이어가 여러 층으로 감기면서 유효 반경이 달라질 수 있으므로 단순한 고정 반경 계산만으로 정확한 크기가 보장된다고 가정하지 않는다. 실제 추정식과 허용 오차는 기구 측정 및 calibration으로 검증한다.

### 로봇 통합 제어 명령(Robot control command)

`RobotControlCommand` 하나는 PC가 로봇 보드로 한 번에 보내는 최상위 명령이다.

- protocol version과 명령 sequence 번호
- 명령에 포함된 가변 휠 개수
- 등록된 각 `wheel_id`의 `WheelControlCommand`
- 필요 시 명령 유효 시간

PC는 등록된 가변 휠의 누락, 중복 ID 및 각 모터 제어값의 범위를 전체 검증한 뒤 명령 하나를 직렬화한다. 일부 항목이 유효하지 않으면 불완전한 명령을 보내지 않는다. encoder count와 실제 가변 휠 크기의 변환식은 기구 설계와 calibration 결과가 나온 뒤 설정값으로 추가한다.

이 구조는 **하나의 명령으로 여러 가변 휠의 제어값을 보드에 전달하는 것**까지만 정의한다. 보드가 명령을 해석해 각 가변 휠에 하달하는 방식과 실제 동시 적용 보장은 현재 구현 범위가 아니다.

```text
RobotControlCommand
├─ WheelControlCommand (wheel_id=1)
│  ├─ 주행 모터 제어값
│  └─ 조절 모터 제어값
├─ WheelControlCommand (wheel_id=2)
│  ├─ 주행 모터 제어값
│  └─ 조절 모터 제어값
└─ ... 등록된 나머지 가변 휠
```

### Telemetry와 상태

PC가 감시할 최소 상태는 다음과 같다.

- 연결 상태와 마지막 수신 시각
- 각 가변 휠의 주행 모터 command 상태
- 조절 모터 encoder position
- 영점 기준 상대 위치와 telemetry 기준 시각
- 와이어 감김량 및 가변 휠 크기 추정값
- 위치 추정의 calibration·유효성 상태
- 크기 조절 동작 상태
- limit 접근 또는 초과 상태
- timeout, protocol 오류 및 board fault

## 6. 초기 ASCII protocol 원칙

ASCII는 초기 개발과 디버깅을 위한 encoding 방식으로 사용한다. application은 문자열을 직접 만들지 않고 protocol codec만 frame 형식을 알아야 한다.

초기 frame은 다음 요구를 만족하도록 설계한다.

- 한 frame은 newline으로 종료한다.
- protocol version, sequence 번호, command type, 가변 휠 개수 및 가변 휠별 payload를 구분한다.
- board는 성공 시 `ACK`, 실패 시 원인 code가 포함된 `NACK`를 반환한다.
- encoder 및 fault 상태는 `TELEMETRY` frame으로 전달한다.
- 알 수 없는 명령, 잘못된 인자, 범위를 벗어난 값 및 손상된 frame을 거부한다.
- 중복 또는 누락된 `wheel_id`와 설정에 없는 ID를 거부한다.
- 숫자의 단위, 범위, 부호 및 소수점 허용 여부를 명시한다.
- protocol 변경을 위해 version field를 둔다.

개념 예시는 다음과 같으며 최종 문법은 hardware interface 확정 후 고정한다.

```text
V1 <seq> ROBOT_CONTROL <wheel_count> WHEEL <wheel_id> DRIVE <signed_speed> ADJUST <target_position> <speed_limit> ...\n
V1 <seq> STOP ALL\n
V1 ACK <seq>\n
V1 NACK <seq> <error_code>\n
V1 TELEMETRY <wheel_id> <encoder_position> <state> <fault>\n
```

가변 휠 두 개를 포함하는 개념 예시는 다음과 같다. 숫자의 의미와 범위는 아직 확정된 protocol 규격이 아니다.

```text
V1 42 ROBOT_CONTROL 2 WHEEL 1 DRIVE 100 ADJUST 320 20 WHEEL 2 DRIVE -100 ADJUST 315 20\n
```

향후 binary protocol로 변경할 때도 `RobotControlCommand`, `WheelControlCommand`, `DriveCommand`, `AdjustmentCommand`, `StopCommand`와 같은 내부 명령 모델은 유지하고 codec만 교체하는 것을 원칙으로 한다.

## 7. 와이어 과인장 방지 원칙

와이어 손상 방지는 단일 조건이 아니라 여러 방어 계층으로 설계한다.

1. 설정된 encoder soft limit 밖의 목표 명령을 PC에서 거부한다.
2. 동작 중 encoder position이 limit 또는 경고 구간에 도달하면 정지 명령을 보낸다.
3. encoder 값이 지정 시간 동안 변하지 않거나 예상 방향과 반대로 움직이면 fault로 전환한다.
4. telemetry가 timeout되거나 연결이 끊기면 크기 조절 동작을 계속하지 않는다.
5. fault가 발생하면 명시적으로 reset하기 전까지 추가 크기 조절 명령을 차단한다.
6. 향후 board firmware에도 동일한 hard/soft limit 및 timeout을 구현한다.
7. 가능하면 기계식 limit switch, motor current 제한 또는 장력 센서를 별도 안전 계층으로 검토한다.

PC의 감시는 통신 단절이나 지연 중에는 모터를 즉시 멈출 수 없다. 따라서 실제 장비의 최종 과인장 방지는 반드시 robot board 또는 motor driver 측에서 독립적으로 수행해야 한다.

초기 상태 모델은 다음을 기준으로 검토한다.

```text
DISCONNECTED -> CONNECTING -> READY -> DRIVING/ADJUSTING
      ^                         |           |
      +-------------------------+-----------+
                                |
                                v
                              FAULT
```

`STOP`과 emergency stop은 일반 명령보다 우선하며, 연결 복구만으로 `FAULT` 상태를 자동 해제하지 않는다.

## 8. 다중 가변 휠 제어 방향

현재 PC-to-board 연결부터 구현하되, 다음 확장을 전제로 한다.

- PC는 가변 휠 개수와 배치를 설정으로 읽는다.
- 사용자 이동 명령은 motion coordinator에서 가변 휠별 주행 모터 값으로 변환한다.
- 각 가변 휠의 주행 모터 값과 조절 모터 값을 하나의 `WheelControlCommand`로 묶는다.
- 등록된 모든 `WheelControlCommand`를 하나의 `RobotControlCommand`로 묶어 보드에 한 번 전송한다.
- robot board가 통합 명령을 각 가변 휠 controller에 재분배하는 기능은 향후 단계로 둔다.
- 한 가변 휠의 fault가 전체 정지로 이어질지 격리 운전으로 이어질지는 안전 분석 후 정책으로 정한다.
- 모든 가변 휠의 실제 명령 적용 시점과 동기화 보장은 board 기능과 실제 주행 시험 단계에서 결정한다.

## 9. 개발 전제와 검증 환경

하드웨어가 없는 기간에는 mock transport와 board simulator를 사용한다. simulator는 정상 ACK뿐 아니라 encoder 변화, encoder limit, 응답 지연, 연결 끊김, 잘못된 frame 및 fault telemetry를 재현해야 한다. 단일 가변 휠 시험 UI도 먼저 이 simulator에 연결해 주행·조절 입력과 위치 표시 흐름을 검증한다.

실제 robot board가 준비되기 전까지 PC-to-board 연결 완료를 주장하지 않는다. 단계별 개발 순서와 완료 조건은 [TODO_LIST.md](TODO_LIST.md)에만 기록한다.

## 10. 현재 확인이 필요한 사항

- PC와 robot board 사이의 물리 연결 방식 및 통신 library
- robot board, motor driver 및 encoder의 정확한 모델
- encoder resolution, gear ratio, 회전 방향과 영점 설정 방법
- spool 초기 반경, 와이어 직경과 감김에 따른 유효 반경 변화
- 와이어 감김량과 실제 가변 휠 크기의 calibration 관계 및 허용 오차
- 안전한 encoder 최소·최대값과 경고 여유값
- 주행 모터 속도 단위, 최대값 및 feedback 유무
- 가변 휠 개수, 번호, 장착 방향, roller 각도와 좌표계
- 통합 명령에서 조절 모터 값을 유지하거나 변경하지 않을 때의 표현
- 상하·좌우 이동의 기준 좌표계와 요구 자유도
- heartbeat 주기, telemetry 주기 및 timeout
- emergency stop의 hardware 구성과 복구 절차

이 값들은 현재 자료만으로 확인할 수 없으므로 임의로 고정하지 않는다.
