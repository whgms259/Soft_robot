"""가변 휠 시험 UI에서 사용하는 상태와 simulation 계산."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


GAUGE_DISPLAY_MIN = 0.0
GAUGE_DISPLAY_MAX = 10.0
WINDING_MIN = 0.5
WINDING_MAX = 9.5
WINDING_SPEED_MIN = 0.1
WINDING_SPEED_MAX = 1.0
WINDING_SPEED_STEP = 0.1
UPDATE_INTERVAL_MS = 50


class DriveDirection(str, Enum):
    """주행 모터 회전 방향."""

    FORWARD = "+"
    REVERSE = "-"


class AdjustmentDirection(str, Enum):
    """조절 모터의 와이어 동작 방향."""

    WIND = "감기"
    UNWIND = "풀기"


@dataclass(frozen=True, slots=True)
class WheelUiState:
    """UI가 표현하는 단일 가변 휠의 현재 제어 상태."""

    drive_enabled: bool = False
    drive_direction: DriveDirection = DriveDirection.FORWARD
    adjustment_enabled: bool = False
    adjustment_direction: AdjustmentDirection = AdjustmentDirection.UNWIND

    def status_lines(self) -> tuple[str, str, str, str]:
        """화면 표시용 상태 문구를 반환한다."""

        return (
            f"주행 모터: {'ON' if self.drive_enabled else 'OFF'}",
            f"주행 방향: {self.drive_direction.value}",
            f"조절 모터: {'ON' if self.adjustment_enabled else 'OFF'}",
            f"조절 방향: {self.adjustment_direction.value}",
        )


@dataclass(frozen=True, slots=True)
class WindingGaugeState:
    """조절 모터의 시뮬레이션 감김 위치와 선택 목표."""

    current: float = WINDING_MIN
    target: float | None = None

    def with_target(self, value: float) -> WindingGaugeState:
        """표시 범위에서 선택한 값을 실제 이동 가능 범위로 제한한다."""

        return WindingGaugeState(self.current, clamp_winding(value))

    def advance_manual(
        self,
        direction: AdjustmentDirection,
        elapsed_seconds: float,
        speed: float = WINDING_SPEED_MIN,
    ) -> WindingGaugeState:
        """현재 방향과 경과 시간에 따라 수동 운전 위치를 갱신한다."""

        delta = speed * max(0.0, elapsed_seconds)
        if direction is AdjustmentDirection.UNWIND:
            delta = -delta
        return WindingGaugeState(
            clamp_winding(self.current + delta),
            self.target,
        )

    def advance_toward_target(
        self,
        elapsed_seconds: float,
        speed: float = WINDING_SPEED_MIN,
    ) -> WindingGaugeState:
        """목표를 지나치지 않도록 시간 기반으로 현재 위치를 이동한다."""

        if self.target is None or self.is_at_target:
            return self

        step = speed * max(0.0, elapsed_seconds)
        distance = self.target - self.current
        movement = min(abs(distance), step)
        if distance < 0:
            movement = -movement
        return WindingGaugeState(self.current + movement, self.target)

    @property
    def is_at_target(self) -> bool:
        return self.target is not None and abs(self.current - self.target) < 1e-9


def clamp_winding(value: float) -> float:
    """감김 위치를 simulation 이동 범위로 제한한다."""

    return min(WINDING_MAX, max(WINDING_MIN, value))


def clamp_winding_speed(value: float) -> float:
    """이동 속도를 허용 범위와 0.1 단위로 제한한다."""

    clamped = min(WINDING_SPEED_MAX, max(WINDING_SPEED_MIN, value))
    return round(clamped, 1)
