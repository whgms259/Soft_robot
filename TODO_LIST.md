# 작업 절차 및 TODO LIST

## 문서 목적

이 문서는 가변 휠 제어 시스템을 **어떤 단계와 순서로 개발할지** 정의하고 세부 작업 진행도와 단계별 완료 조건을 관리한다. 프로젝트의 목적, 설계 내용과 현재 작업·구현 현황은 `README.md`, 작업자의 행동 지침은 `AGENTS.md`를 따른다.

매 작업은 `AGENTS.md → README.md → TODO_LIST.md` 순서로 읽은 뒤 시작한다. README에 기록된 현재 상태를 기준으로 이 문서의 완료·미완료·보류 항목을 대조해 다음 작업을 결정한다.

작업은 원칙적으로 0단계부터 순서대로 진행한다. 후속 단계가 선행 hardware나 결정에 의존하지 않고 독립적으로 검증 가능할 때만 병행한다.

첫 software milestone은 `1 → 1.1 → 1.2` 순서로 진행해 단일 가변 휠 command, mock 위치 추정과 시험 UI를 완성한다. 이후 `2 → 5` 단계에서 실제 통신과 encoder 연동을 검증하고, 다중 가변 휠 기능은 그 다음 단계에서 확장한다.

상태 표기:

- `[x]`: 완료 및 검토됨
- `[ ]`: 미착수 또는 진행 중
- `[보류]`: 선행 정보나 hardware가 필요함

## 0. 요구사항 및 설계 기준선

- [x] 프로젝트 목적과 현재 PC-to-board 범위를 정리한다.
- [x] 가변 휠당 주행 모터 1개와 encoder가 있는 조절 모터 1개를 기본 hardware 모델로 정리한다.
- [x] ASCII 초기 protocol과 교체 가능한 transport/codec 구조를 설계 원칙으로 정한다.
- [x] 향후 2개 이상의 가변 휠과 UI를 수용할 확장 방향을 문서화한다.
- [x] 등록된 모든 가변 휠의 두 모터 제어값을 하나의 명령으로 보드에 전달하는 요구사항을 정리한다.
- [x] 첫 코드 구현 대상을 단일 가변 휠의 두 모터 제어 module로 확정한다.
- [x] 단일 가변 휠 시험용 UI에서 주행 모터 방향·속도, 조절 모터와 encoder 위치 추정을 확인하는 목표를 정리한다.
- [x] PC 감시와 board-side 독립 안전 제어의 책임을 구분한다.
- [x] 매 작업의 기본 행동·설계·안전 기준을 `AGENTS.md`에 정의한다.
- [ ] PC와 robot board 사이의 물리 통신 방식 후보를 비교하고 하나를 선정한다.
- [ ] robot board, motor driver, encoder 모델과 electrical interface를 확정한다.
- [ ] 주행 모터의 feedback 제공 여부와 제어 단위를 확정한다.
- [ ] 가변 휠 좌표계, 번호 체계, 개수와 장착 방향을 확정한다.
- [ ] 상하·좌우 이동이 의미하는 기준 좌표계와 필요한 자유도를 확정한다.
- [x] local Git 저장소를 `main` branch로 초기화한다.
- [x] GitHub `whgms259/Soft_robot` 저장소를 `origin`으로 연결한다.
- [x] GitHub 일반 파일 크기 제한을 초과하는 kickoff PDF를 사용자 요청에 따라 삭제한다.
- [x] Python cache, 가상환경, IDE 설정과 test 산출물을 `.gitignore`로 제외한다.
- [ ] Git commit 작성자 이름·email을 설정하고 initial commit을 `origin/main`에 push한다.

완료 조건: 미정 hardware/interface 항목이 기록되어야 한다. hardware와 독립적인 단일 가변 휠 module은 명시적인 test 설정을 주입해 먼저 진행할 수 있으며, 실제 통신과 motor 제어는 연결 방식과 안전값이 승인된 뒤 진행한다.

## 1. 프로젝트 골격과 단일 가변 휠 제어 module — 최우선 구현

- [x] 초기 UI prototype의 실행 환경을 Python 3.12로 결정한다.
- [x] 현재 구현에 필요한 `src/ui`와 `tests` package만 생성한다.
- [ ] `WheelId`, `DriveCommand`, `AdjustmentCommand`, `WheelControlCommand`의 최소 domain model을 정의한다.
- [ ] 가변 휠 하나의 두 모터 명령 생성을 담당하는 `VariableWheelController` interface를 정의한다.
- [ ] module 생성 시 제어 대상 `wheel_id`를 지정하도록 한다.
- [ ] 주행 모터와 조절 모터 입력을 한 번의 호출로 받아 `WheelControlCommand` 하나를 생성한다.
- [ ] 주행 모터 출력 범위, 조절 모터 encoder limit과 timeout 설정을 외부에서 주입할 수 있게 한다.
- [ ] 누락된 값, 잘못된 자료형과 설정 범위를 벗어난 값을 거부한다.
- [ ] hardware 사양으로 오해되지 않는 명시적 test 설정을 사용한다.
- [ ] 정상 입력, 각 모터의 경계값, 잘못된 `wheel_id`와 잘못된 입력에 대한 unit test를 작성한다.
- [ ] 통신, `RobotControlCommand` 조립 및 board 내부 분배가 이 module에 포함되지 않았는지 검토한다.
- [ ] 공개 interface와 각 모듈의 책임을 README에 반영한다.

완료 조건: 통신 장치 없이 특정 `wheel_id`의 주행 모터·조절 모터 입력을 검증해 `WheelControlCommand` 하나로 생성할 수 있어야 한다. module을 두 개 이상 독립 생성해도 상태가 섞이지 않아야 하며 관련 unit test가 통과해야 한다.

## 1.1. Encoder 기반 현재 위치 추정 — 단일 휠 milestone

- [ ] encoder 원시 count, timestamp와 유효성 상태 model을 정의한다.
- [ ] 영점 기준 상대 encoder position을 계산하는 `WheelPositionEstimator` interface를 정의한다.
- [ ] encoder resolution과 gear ratio를 외부 설정으로 주입한다.
- [ ] spool 유효 반경을 이용한 회전량-와이어 감김량 변환 interface를 정의한다.
- [ ] 와이어 감김량-가변 휠 크기 calibration을 교체 가능한 table 또는 함수로 정의한다.
- [ ] 영점 미설정, calibration 미완료, 오래된 telemetry와 잘못된 encoder 값을 구분한다.
- [ ] 위치 증가·감소 방향, 알려진 count 변화, 영점 재설정과 경계값 unit test를 작성한다.
- [ ] mock encoder sequence에서 예상 상대 위치와 와이어 감김량이 계산되는지 시험한다.

완료 조건: 실제 hardware 없이도 주어진 encoder sequence에서 원시 count, 영점 기준 위치, 와이어 감김량 및 가변 휠 크기 추정 상태를 재현할 수 있어야 한다. calibration이 없으면 정확한 크기 대신 미보정 상태를 반환해야 한다.

## 1.2. 단일 가변 휠 시험 UI — 단일 휠 milestone

- [x] 첫 UI 범위를 네 개의 기본 토글로 정의한다.
- [x] 주행 모터 `OFF/ON` 토글을 만든다.
- [x] 주행 방향 `+/-` 토글을 만든다.
- [ ] 주행 모터 목표 속도 입력 control을 만든다.
- [x] 조절 모터 `OFF/ON` 토글을 만든다.
- [x] 조절 모터 감기/풀기 토글을 만든다.
- [x] 0~10 눈금에서 0.5~9.5 범위를 선택하는 조절 모터 simulation 목표 위치 control을 만든다.
- [x] 현재 위치는 파란색 짧은 선과 아래 `▲`, 목표는 빨간색 짧은 선과 위 `▼`, 목표 도달은 보라색으로 표시한다.
- [x] mouse drag 중 목표를 미리 표시하고 button을 놓을 때만 목표를 확정한다.
- [x] 조절 모터 수동 운전과 목표 이동 속도를 0.1~1.0 범위에서 0.1 단위로 조절한다.
- [x] `이동`을 누르면 방향과 가동 상태를 자동 설정하고 도달 시 조절 모터를 정지한다.
- [x] 목표 이동 중 `이동`을 `멈춤`으로 전환하고, 누르면 현재 위치에서 정지한 뒤 다시 `이동`으로 복원한다.
- [x] `초기화`를 누르면 목표를 현재 감김 위치로 되돌리고 이동을 정지한다.
- [ ] encoder 원시값, 영점 기준 위치, 와이어 감김량과 가변 휠 크기 추정값을 표시한다.
- [ ] 위치 추정의 정상·미보정·오류·telemetry timeout 상태를 구분해 표시한다.
- [ ] 연결 상태, 현재 명령, limit와 fault 상태를 표시한다.
- [x] UI가 protocol/transport를 직접 호출하지 않고 `WheelUiState` callback만 노출하도록 한다.
- [ ] mock controller와 encoder telemetry로 UI 동작을 검증한다.
- [x] 네 토글의 기본 선택값을 왼쪽(`OFF`, `+`, `OFF`, `풀기`)으로 통일한다.
- [x] UI framework로 Python 표준 `tkinter`를 선정한다.
- [x] 기본 상태와 네 제어 상태 표시의 unit test를 작성한다.
- [x] 감김 위치·속도 범위 제한, 선택 속도 적용과 목표 초과 방지 unit test를 작성한다.
- [x] 숨김 상태의 UI 초기화에서 네 개 토글 생성과 화면 요구 크기를 검증한다.
- [x] 현재 작업 폴더와 무관하게 실행할 수 있는 `run_ui.py` launcher를 추가한다.
- [x] project 외부 폴더에서 launcher import 검사를 수행한다.
- [x] refactoring 전 backup을 생성하고 검증 완료 후 사용자 요청에 따라 삭제한다.
- [x] UI 상태·widget·화면 제어를 별도 module로 분리하고 `app.py`를 호환 진입점으로 간소화한다.
- [x] module 분리 후 기존 unit test와 Tk interaction 회귀 시험을 수행한다.
- [x] `app.py`를 project root로 이동하고 `src/ui/`에는 재사용 module만 유지한다.
- [x] code·test·문서의 고정 절대경로를 제거하고 project root 기준 상대 구조로 정리한다.
- [x] project를 임시 위치에 복사한 뒤 복사본의 `app.py --check`를 실행하는 portability 회귀 시험을 추가한다.

완료 조건: mock 환경에서 UI로 선택한 단일 가변 휠의 주행 모터 방향·속도와 조절 모터 명령을 만들 수 있고, encoder 변화에 따라 위치 추정 표시가 갱신되어야 한다. 미보정 또는 끊긴 telemetry를 정상값처럼 표시하지 않아야 한다.

## 2. 교체 가능한 통신 계층

- [ ] `Transport` interface의 connect, disconnect, send, receive 계약을 정의한다.
- [ ] hardware 없이 시험할 `MockTransport`를 구현한다.
- [ ] 실제 선정된 연결 방식의 transport adapter를 구현한다.
- [ ] 연결 상태, 재연결, read/write timeout과 종료 절차를 구현한다.
- [ ] 상위 application code가 구체 transport class에 직접 의존하지 않는지 검토한다.

완료 조건: 같은 application test를 mock과 실제 transport adapter에 공통 적용할 수 있어야 한다.

## 3. ASCII protocol V1

- [ ] 명령/응답 frame 문법, delimiter, encoding, 최대 길이와 newline 규칙을 확정한다.
- [ ] version, sequence, 가변 휠 개수와 가변 휠별 두 모터 payload field를 정의한다.
- [ ] 속도·encoder 값의 단위, 범위와 부호 규칙을 확정한다.
- [ ] `ROBOT_CONTROL`, `WHEEL`, `DRIVE`, `ADJUST`, `STOP`, `ACK`, `NACK`, `TELEMETRY` frame을 정의한다.
- [ ] 조절 모터 값을 유지하거나 변경하지 않을 때의 protocol 표현을 정의한다.
- [ ] encoder/decoder와 streaming parser를 구현한다.
- [ ] 가변 휠 개수에 따른 최대 frame 길이와 허용 최대 가변 휠 수를 확정한다.
- [ ] partial frame, 연속 frame, 잘못된 UTF/ASCII, 초과 길이 및 알 수 없는 명령을 시험한다.
- [ ] 가변 휠 누락, 중복 ID, 알 수 없는 ID와 개수 불일치 frame을 시험한다.
- [ ] sequence를 이용한 요청-응답 대응 및 timeout 처리를 구현한다.
- [ ] protocol 규격 변경 시 version 호환 정책을 문서화한다.
- [ ] `WheelControlCommand` 한 개만 포함한 `RobotControlCommand`도 같은 frame 구조로 표현되는지 시험한다.

완료 조건: 정상·경계·오류 frame에 대한 unit test가 통과하고, codec 교체 없이 domain/application code가 문자열 형식에 의존하지 않아야 한다.

## 4. 통합 명령 생성과 PC-to-board 송신

- [ ] 1단계에서 구현한 `VariableWheelController`와 `WheelControlCommand`를 변경 없이 재사용한다.
- [ ] `RobotControlCommand`와 `StopCommand` 모델을 정의한다.
- [ ] ACK/NACK, telemetry, connection 및 fault 상태 모델을 정의한다.
- [ ] 가변 휠 수, timeout과 통신 설정 schema를 정의한다.
- [ ] 가변 휠 하나만 등록한 test 설정으로 `wheel_count=1` 명령을 생성한다.
- [ ] 단일 가변 휠 명령을 mock board에 보내고 해당 `wheel_id`의 telemetry를 application service로 되돌린다.
- [ ] 단일 가변 휠 시험 UI가 application service를 통해 명령 전송과 telemetry 갱신을 수행하는지 확인한다.
- [ ] 등록된 가변 휠의 누락, 잘못된 범위, 알 수 없는 ID 및 중복 ID를 거부하는 통합 validation을 추가한다.
- [ ] 등록된 모든 `WheelControlCommand`를 하나의 `RobotControlCommand`로 조립한다.
- [ ] 모든 가변 휠의 명령을 전체 검증한 뒤 ASCII frame 하나로 직렬화한다.
- [ ] 유효하지 않은 가변 휠 항목이 하나라도 있으면 전체 통합 명령 전송을 거부한다.
- [ ] 통합 명령과 전체 정지 명령을 PC에서 보드로 전송한다.
- [ ] 통합 명령 단위 ACK/NACK와 가변 휠별 telemetry를 반환하는 board simulator를 구현한다.
- [ ] 지연 응답, 무응답, 연결 끊김, 손상 frame 및 board fault scenario를 추가한다.
- [ ] CLI 또는 test harness로 명령 송수신을 확인한다.
- [보류] 실제 robot board에서 PC 명령 수신과 ACK 반환을 확인한다.

완료 조건: 먼저 mock 환경에서 가변 휠 하나의 두 모터 제어값과 encoder telemetry가 UI까지 왕복해야 한다. 그다음 2개 이상의 가변 휠 제어값이 단일 frame으로 전송되고 응답·timeout·오류가 올바른 상태로 변환되어야 한다. 잘못된 가변 휠 항목이 포함된 명령은 일부만 전송되지 않고 전체 거부되어야 한다. 실제 board가 준비되면 동일 scenario의 smoke test를 통과해야 한다.

## 5. 실제 encoder 연동, 위치 추정 검증 및 크기 조절 안전

- [ ] encoder의 resolution, gear ratio, 방향과 기준 영점 절차를 확정한다.
- [ ] spool 반경, 와이어 직경과 감김 층에 따른 유효 반경 모델을 확정한다.
- [ ] 안전 최소/최대 position, 경고 구간과 허용 오차를 측정해 설정한다.
- [ ] 목표 position이 soft limit를 넘으면 송신 전에 거부한다.
- [ ] limit 접근 시 감속 또는 정지하는 정책을 확정한다.
- [ ] encoder 미변화(stall), 역방향 변화, 비정상 점프를 검출한다.
- [ ] telemetry timeout과 연결 단절 시 조절 모터 정지를 요청하고 `FAULT`로 전환한다.
- [ ] fault latch, 명시적 reset 및 안전한 homing 절차를 구현한다.
- [ ] encoder count와 실제 wheel 크기의 calibration table 또는 함수를 구현한다.
- [ ] 알려진 조절 위치에서 추정값과 실제 와이어 감김량·가변 휠 크기를 비교한다.
- [ ] 위치 추정 오차와 허용 범위를 정하고 정상 적용 여부를 판정한다.
- [ ] 실제 telemetry가 UI의 원시값·상대 위치·추정 크기에 올바르게 반영되는지 확인한다.
- [ ] 정상 조절, 상·하한, stall, 단선/무응답 및 복구 test를 작성한다.
- [보류] board firmware에 독립적인 encoder limit, timeout 및 emergency stop을 구현한다.
- [보류] 기계식 limit switch, motor current 제한 또는 장력 센서 적용 여부를 결정한다.

완료 조건: simulator의 모든 과인장 위험 scenario에서 추가 인장 명령이 차단되고 정지/fault 상태가 관찰되어야 한다. 실제 장비에서는 알려진 위치별 추정 오차가 확정된 허용 범위 안에 있고 UI 표시와 일치해야 한다. board-side 보호 시험도 별도로 통과해야 한다.

## 6. 다중 가변 휠 이동 제어

- [ ] 설정으로 2개 이상의 가변 휠을 등록하고 상태를 독립 관리한다.
- [ ] 사용자 이동 벡터와 robot 좌표계를 정의한다.
- [ ] 가변 휠 배치와 roller 각도를 반영하는 kinematics/mixing 모델을 결정한다.
- [ ] 이동 입력을 가변 휠별 방향과 목표 속도로 변환하는 motion coordinator를 구현한다.
- [ ] 속도 saturation과 전체 비율 보존 정책을 구현한다.
- [ ] motion coordinator의 결과를 기존 `RobotControlCommand`에 결합한다.
- [ ] 여러 가변 휠에 적용할 명령의 동기화 요구와 적용 시점을 결정한다.
- [ ] 개별 가변 휠 fault 발생 시 전체 정지 또는 격리 정책을 결정한다.
- [ ] 전후·상하·좌우 입력에 대한 방향·속도 mapping test를 작성한다.
- [보류] robot board의 가변 휠별 명령 재분배 기능을 구현한다.
- [보류] robot board와 가변 휠 controller 사이의 분배 protocol을 정의한다.
- [보류] 실제 하드웨어에서 이동 방향, 속도 및 미끄럼을 calibration한다.

완료 조건: 확정된 가변 휠 구성에서 각 이동 입력의 기대 가변 휠 방향·속도가 자동 test와 실제 주행 시험에서 일치해야 한다.

## 7. 운용 안전과 관측성

- [ ] heartbeat, telemetry 주기와 connection timeout을 확정한다.
- [ ] 일반 `STOP`과 emergency stop의 우선순위 및 전달 경로를 정의한다.
- [ ] 명령 sequence, wheel 상태, encoder 값, warning과 fault를 구조화해 기록한다.
- [ ] 로그에 protocol 원문을 남길 범위와 민감 정보 정책을 정한다.
- [ ] 시작, 정상 종료, 비정상 종료 및 재연결 시 motor 안전 상태를 검증한다.
- [보류] hardware emergency stop과 motor driver fail-safe 동작을 시험한다.

완료 조건: 통신 단절과 프로그램 종료를 포함한 정의된 fault scenario에서 위험한 동작이 지속되지 않고 원인을 추적할 수 있어야 한다.

## 8. 다중 가변 휠 통합 UI 확장 — 향후 단계

- [ ] 단일 가변 휠 시험 UI를 재사용해 다중 가변 휠 작업 흐름과 화면을 확장한다.
- [ ] 연결 상태, 가변 휠별 속도, encoder position, 크기와 fault 표시 항목을 정한다.
- [ ] 전후·상하·좌우 조작, 개별 가변 휠 시험, 크기 조절 및 정지 control을 설계한다.
- [ ] UI가 protocol/transport를 직접 호출하지 않고 application service만 사용하도록 한다.
- [ ] emergency stop을 항상 접근 가능한 위치에 배치한다.

완료 조건: 여러 가변 휠의 상태와 통합 이동 명령을 한 화면에서 구분해 제어하고, 개별 또는 전체 fault와 정지 상태를 명확히 확인할 수 있어야 한다. 현재는 구현하지 않는다.

## 9. 각 단계의 공통 마감 절차

각 단계의 작업 항목을 완료한 뒤 다음 순서로 마감한다.

1. 변경된 구현을 자체 검토한다.
2. 해당 단계의 unit/integration test 또는 가능한 수동 검증을 수행한다.
3. 단계의 완료 조건을 실제로 충족했는지 확인한다.
4. 새로 구현된 기능과 확인된 제한을 `README.md`에 반영한다.
5. 완료·미완료·보류 상태를 이 문서에 갱신한다.
6. 문제를 수정했다면 root cause, 해결 방법과 남은 제한을 기록한다.
7. 다음 단계의 선행 조건이 충족됐는지 확인한 뒤 진행한다.
