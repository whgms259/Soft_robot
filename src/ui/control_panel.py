"""단일 가변 휠 시험 화면의 조립과 interaction 제어."""

from __future__ import annotations

from time import monotonic
import tkinter as tk
from tkinter import ttk
from typing import Callable

from .models import (
    UPDATE_INTERVAL_MS,
    WINDING_SPEED_MIN,
    WINDING_SPEED_STEP,
    AdjustmentDirection,
    DriveDirection,
    WheelUiState,
    WindingGaugeState,
    clamp_winding_speed,
)
from .widgets import ToggleSwitch, WindingGauge


class VariableWheelControlApp(ttk.Frame):
    """단일 가변 휠의 기본 상태와 감김 위치를 조작하는 화면."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        on_state_change: Callable[[WheelUiState], None] | None = None,
    ) -> None:
        super().__init__(master, padding=24)
        self._on_state_change = on_state_change
        self._winding_state = WindingGaugeState()
        self._winding_speed = WINDING_SPEED_MIN
        self._moving_to_target = False
        self._last_update = monotonic()
        self._configure_styles()
        self._build_widgets()
        self._update_status()
        self.after(UPDATE_INTERVAL_MS, self._update_winding_position)

    @property
    def state(self) -> WheelUiState:
        return WheelUiState(
            drive_enabled=self._drive_enabled.is_right,
            drive_direction=(
                DriveDirection.REVERSE
                if self._drive_direction.is_right
                else DriveDirection.FORWARD
            ),
            adjustment_enabled=self._adjustment_enabled.is_right,
            adjustment_direction=(
                AdjustmentDirection.WIND
                if self._adjustment_direction.is_right
                else AdjustmentDirection.UNWIND
            ),
        )

    @property
    def winding_state(self) -> WindingGaugeState:
        return self._winding_state

    @property
    def winding_speed(self) -> float:
        return self._winding_speed

    @property
    def is_moving_to_target(self) -> bool:
        return self._moving_to_target

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.configure("Title.TLabel", font=("맑은 고딕", 18, "bold"))
        style.configure("Subtitle.TLabel", foreground="#6b7280")
        style.configure("Section.TLabelframe.Label", font=("맑은 고딕", 12, "bold"))
        style.configure("ControlLabel.TLabel", font=("맑은 고딕", 10))
        style.configure("Status.TLabel", font=("맑은 고딕", 10))

    def _build_widgets(self) -> None:
        self.pack(fill=tk.BOTH, expand=True)
        self._build_header()

        controls = ttk.Frame(self)
        controls.pack(fill=tk.BOTH, expand=True)
        controls.columnconfigure((0, 1), weight=1, uniform="motor")
        self._build_drive_controls(controls)
        self._build_adjustment_controls(controls)
        self._build_status()

    def _build_header(self) -> None:
        ttk.Label(self, text="가변 휠 기본 제어", style="Title.TLabel").pack(
            anchor=tk.W
        )
        ttk.Label(
            self,
            text="UI 상태 확인용 · 하드웨어 미연결",
            style="Subtitle.TLabel",
        ).pack(anchor=tk.W, pady=(4, 20))

    def _build_drive_controls(self, master: ttk.Frame) -> None:
        frame = self._motor_frame(master, "주행 모터", column=0, padx=(0, 8))
        self._drive_enabled = self._toggle(
            frame,
            title="가동 상태",
            left="OFF",
            right="ON",
            command=self._update_status,
        )
        self._drive_enabled.pack(fill=tk.X, pady=(0, 18))
        self._drive_direction = self._toggle(
            frame,
            title="회전 방향",
            left="+",
            right="-",
            command=self._update_status,
        )
        self._drive_direction.pack(fill=tk.X)

    def _build_adjustment_controls(self, master: ttk.Frame) -> None:
        frame = self._motor_frame(master, "조절 모터", column=1, padx=(8, 0))
        self._adjustment_enabled = self._toggle(
            frame,
            title="가동 상태",
            left="OFF",
            right="ON",
            command=self._on_adjustment_enabled_changed,
        )
        self._adjustment_enabled.pack(fill=tk.X, pady=(0, 18))
        self._adjustment_direction = self._toggle(
            frame,
            title="와이어 방향",
            left="풀기",
            right="감기",
            command=self._on_adjustment_direction_changed,
        )
        self._adjustment_direction.pack(fill=tk.X, pady=(0, 18))

        self._winding_gauge = WindingGauge(
            frame,
            state=self._winding_state,
            on_target_change=self._set_winding_target,
        )
        self._winding_gauge.pack(fill=tk.X)
        self._build_target_buttons(frame)
        self._build_speed_control(frame)

    def _motor_frame(
        self,
        master: ttk.Frame,
        title: str,
        *,
        column: int,
        padx: tuple[int, int],
    ) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(
            master,
            text=title,
            padding=18,
            style="Section.TLabelframe",
        )
        frame.grid(row=0, column=column, sticky="nsew", padx=padx)
        return frame

    def _toggle(
        self,
        master: tk.Misc,
        *,
        title: str,
        left: str,
        right: str,
        command: Callable[[], None],
    ) -> ToggleSwitch:
        return ToggleSwitch(
            master,
            title=title,
            left_text=left,
            right_text=right,
            initial_right=False,
            command=command,
        )

    def _build_target_buttons(self, master: ttk.LabelFrame) -> None:
        frame = ttk.Frame(master)
        frame.pack(fill=tk.X, pady=(10, 0))
        frame.columnconfigure((0, 1), weight=1, uniform="target")

        self._target_movement_text = tk.StringVar(value="이동")
        self._target_movement_button = ttk.Button(
            frame,
            textvariable=self._target_movement_text,
            command=self._toggle_target_movement,
        )
        self._target_movement_button.grid(
            row=0, column=0, sticky="ew", padx=(0, 4)
        )
        ttk.Button(
            frame,
            text="초기화",
            command=self._reset_winding_target,
        ).grid(row=0, column=1, sticky="ew", padx=(4, 0))

    def _build_speed_control(self, master: ttk.LabelFrame) -> None:
        ttk.Label(
            master,
            text="이동 속도",
            style="ControlLabel.TLabel",
        ).pack(anchor=tk.W, pady=(14, 7))
        frame = ttk.Frame(master)
        frame.pack(fill=tk.X)
        frame.columnconfigure(1, weight=1)
        ttk.Button(
            frame,
            text="◀",
            width=4,
            command=lambda: self._change_winding_speed(-WINDING_SPEED_STEP),
        ).grid(row=0, column=0)
        self._winding_speed_text = tk.StringVar(value=f"{self._winding_speed:.1f}")
        ttk.Label(
            frame,
            textvariable=self._winding_speed_text,
            anchor=tk.CENTER,
            style="Status.TLabel",
        ).grid(row=0, column=1, sticky="ew")
        ttk.Button(
            frame,
            text="▶",
            width=4,
            command=lambda: self._change_winding_speed(WINDING_SPEED_STEP),
        ).grid(row=0, column=2)

    def _build_status(self) -> None:
        frame = ttk.LabelFrame(
            self,
            text="현재 UI 상태",
            padding=14,
            style="Section.TLabelframe",
        )
        frame.pack(fill=tk.X, pady=(18, 0))
        self._status_text = tk.StringVar()
        ttk.Label(
            frame,
            textvariable=self._status_text,
            style="Status.TLabel",
            justify=tk.LEFT,
        ).pack(anchor=tk.W)

    def _update_status(self) -> None:
        current_state = self.state
        self._status_text.set("  ·  ".join(current_state.status_lines()))
        if self._on_state_change is not None:
            self._on_state_change(current_state)

    def _on_adjustment_enabled_changed(self) -> None:
        if not self._adjustment_enabled.is_right:
            self._set_target_movement_active(False)
        self._update_status()

    def _on_adjustment_direction_changed(self) -> None:
        self._set_target_movement_active(False)
        self._update_status()

    def _set_winding_target(self, target: float) -> None:
        self._winding_state = self._winding_state.with_target(target)
        if self._moving_to_target:
            self._set_target_movement_active(False)
            self._adjustment_enabled.set_right(False, notify=False)
            self._update_status()
        self._winding_gauge.set_state(self._winding_state)

    def _reset_winding_target(self) -> None:
        self._winding_state = self._winding_state.with_target(
            self._winding_state.current
        )
        self._set_target_movement_active(False)
        self._adjustment_enabled.set_right(False, notify=False)
        self._winding_gauge.set_state(self._winding_state)
        self._update_status()

    def _change_winding_speed(self, delta: float) -> None:
        self._winding_speed = clamp_winding_speed(self._winding_speed + delta)
        self._winding_speed_text.set(f"{self._winding_speed:.1f}")

    def _set_target_movement_active(self, active: bool) -> None:
        self._moving_to_target = active
        self._target_movement_text.set("멈춤" if active else "이동")

    def _toggle_target_movement(self) -> None:
        if self._moving_to_target:
            self._stop_target_movement()
            return
        self._start_target_movement()

    def _stop_target_movement(self) -> None:
        self._set_target_movement_active(False)
        self._adjustment_enabled.set_right(False, notify=False)
        self._update_status()

    def _start_target_movement(self) -> None:
        target = self._winding_state.target
        if target is None:
            return
        if self._winding_state.is_at_target:
            self._stop_target_movement()
            return

        should_wind = target > self._winding_state.current
        self._adjustment_direction.set_right(should_wind, notify=False)
        self._adjustment_enabled.set_right(True, notify=False)
        self._set_target_movement_active(True)
        self._last_update = monotonic()
        self._update_status()

    def _update_winding_position(self) -> None:
        now = monotonic()
        elapsed = now - self._last_update
        self._last_update = now

        if self._adjustment_enabled.is_right:
            if self._moving_to_target:
                self._advance_to_target(elapsed)
            else:
                self._advance_manually(elapsed)
            self._winding_gauge.set_state(self._winding_state)

        self.after(UPDATE_INTERVAL_MS, self._update_winding_position)

    def _advance_to_target(self, elapsed: float) -> None:
        self._winding_state = self._winding_state.advance_toward_target(
            elapsed,
            self._winding_speed,
        )
        if self._winding_state.is_at_target:
            self._stop_target_movement()

    def _advance_manually(self, elapsed: float) -> None:
        self._winding_state = self._winding_state.advance_manual(
            self.state.adjustment_direction,
            elapsed,
            self._winding_speed,
        )
