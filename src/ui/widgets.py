"""가변 휠 시험 화면에서 재사용하는 tkinter 위젯."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from .models import (
    GAUGE_DISPLAY_MAX,
    GAUGE_DISPLAY_MIN,
    WINDING_MAX,
    WINDING_MIN,
    WindingGaugeState,
    clamp_winding,
)


class ToggleSwitch(ttk.Frame):
    """왼쪽/오른쪽 상태를 선택하는 canvas 기반 토글."""

    WIDTH = 220
    HEIGHT = 48

    def __init__(
        self,
        master: tk.Misc,
        *,
        title: str,
        left_text: str,
        right_text: str,
        initial_right: bool,
        command: Callable[[], None],
    ) -> None:
        super().__init__(master)
        self._left_text = left_text
        self._right_text = right_text
        self._is_right = initial_right
        self._command = command

        ttk.Label(self, text=title, style="ControlLabel.TLabel").pack(
            anchor=tk.W, pady=(0, 7)
        )
        self._canvas = tk.Canvas(
            self,
            width=self.WIDTH,
            height=self.HEIGHT,
            background="#ffffff",
            borderwidth=0,
            highlightthickness=2,
            highlightbackground="#d1d5db",
            highlightcolor="#2563eb",
            cursor="hand2",
            takefocus=True,
        )
        self._canvas.pack(fill=tk.X)
        self._canvas.bind("<Button-1>", self._toggle_from_event)
        self._canvas.bind("<space>", self._toggle_from_event)
        self._canvas.bind("<Return>", self._toggle_from_event)
        self._draw()

    @property
    def is_right(self) -> bool:
        return self._is_right

    def toggle(self) -> None:
        self.set_right(not self._is_right)

    def set_right(self, is_right: bool, *, notify: bool = True) -> None:
        if self._is_right == is_right:
            return
        self._is_right = is_right
        self._draw()
        if notify:
            self._command()

    def _toggle_from_event(self, _event: tk.Event[tk.Misc]) -> str:
        self.toggle()
        return "break"

    def _draw(self) -> None:
        self._canvas.delete("all")
        half = self.WIDTH // 2
        selected_left = 2 if not self._is_right else half
        selected_right = half if not self._is_right else self.WIDTH - 2

        self._canvas.create_rectangle(
            2,
            2,
            self.WIDTH - 2,
            self.HEIGHT - 2,
            fill="#e5e7eb",
            outline="",
        )
        self._canvas.create_rectangle(
            selected_left,
            2,
            selected_right,
            self.HEIGHT - 2,
            fill="#2563eb",
            outline="",
        )
        self._canvas.create_text(
            half // 2,
            self.HEIGHT // 2,
            text=self._left_text,
            fill="white" if not self._is_right else "#6b7280",
            font=("맑은 고딕", 10, "bold"),
        )
        self._canvas.create_text(
            half + half // 2,
            self.HEIGHT // 2,
            text=self._right_text,
            fill="white" if self._is_right else "#111827",
            font=("맑은 고딕", 10, "bold"),
        )


class WindingGauge(ttk.Frame):
    """현재 위치와 drag로 선택하는 목표를 표시하는 게이지."""

    WIDTH = 220
    HEIGHT = 112
    X_PADDING = 10
    AXIS_Y = 48

    def __init__(
        self,
        master: tk.Misc,
        *,
        state: WindingGaugeState,
        on_target_change: Callable[[float], None],
    ) -> None:
        super().__init__(master)
        self._state = state
        self._preview_target: float | None = None
        self._on_target_change = on_target_change

        ttk.Label(self, text="현재 감긴 정도", style="ControlLabel.TLabel").pack(
            anchor=tk.W, pady=(0, 7)
        )
        self._canvas = tk.Canvas(
            self,
            width=self.WIDTH,
            height=self.HEIGHT,
            background="#ffffff",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#d1d5db",
            cursor="crosshair",
        )
        self._canvas.pack(fill=tk.X)
        self._canvas.bind("<Button-1>", self._start_target_selection)
        self._canvas.bind("<B1-Motion>", self._preview_target_selection)
        self._canvas.bind("<ButtonRelease-1>", self._finish_target_selection)
        self._value_text = tk.StringVar()
        ttk.Label(
            self,
            textvariable=self._value_text,
            style="Status.TLabel",
        ).pack(anchor=tk.W, pady=(5, 0))
        self.set_state(state)

    def set_state(self, state: WindingGaugeState) -> None:
        self._state = state
        self._draw()
        self._update_value_text()

    def _update_value_text(self) -> None:
        target = self._display_target
        target_text = "미선택" if target is None else f"{target:.2f}"
        if self._preview_target is not None:
            target_text += " (설정 중)"
        self._value_text.set(
            f"현재 {self._state.current:.2f}  ·  목표 {target_text}"
        )

    @property
    def _display_target(self) -> float | None:
        if self._preview_target is not None:
            return self._preview_target
        return self._state.target

    def _value_to_x(self, value: float) -> float:
        usable_width = self.WIDTH - (2 * self.X_PADDING)
        display_range = GAUGE_DISPLAY_MAX - GAUGE_DISPLAY_MIN
        ratio = (value - GAUGE_DISPLAY_MIN) / display_range
        return self.X_PADDING + usable_width * ratio

    def _event_to_value(self, event: tk.Event[tk.Misc]) -> float:
        usable_width = self.WIDTH - (2 * self.X_PADDING)
        ratio = (event.x - self.X_PADDING) / usable_width
        display_value = GAUGE_DISPLAY_MIN + ratio * (
            GAUGE_DISPLAY_MAX - GAUGE_DISPLAY_MIN
        )
        return clamp_winding(display_value)

    def _start_target_selection(self, event: tk.Event[tk.Misc]) -> None:
        self._preview_target = self._event_to_value(event)
        self._refresh_preview()

    def _preview_target_selection(self, event: tk.Event[tk.Misc]) -> None:
        if self._preview_target is None:
            return
        self._preview_target = self._event_to_value(event)
        self._refresh_preview()

    def _refresh_preview(self) -> None:
        self._draw()
        self._update_value_text()

    def _finish_target_selection(self, event: tk.Event[tk.Misc]) -> None:
        if self._preview_target is None:
            return
        target = self._event_to_value(event)
        self._preview_target = None
        self._on_target_change(target)

    def _draw(self) -> None:
        self._canvas.delete("all")
        self._draw_axis()

        current_x = self._value_to_x(self._state.current)
        target = self._display_target
        target_x = None if target is None else self._value_to_x(target)
        targets_overlap = (
            self._preview_target is None
            and target is not None
            and abs(self._state.current - target) < 1e-9
        )

        if targets_overlap:
            self._draw_overlap_marker(current_x)
            return
        if target_x is not None:
            self._draw_target_marker(target_x)
        self._draw_current_marker(current_x)

    def _draw_axis(self) -> None:
        self._canvas.create_rectangle(
            self._value_to_x(WINDING_MIN),
            self.AXIS_Y - 8,
            self._value_to_x(WINDING_MAX),
            self.AXIS_Y + 8,
            fill="#eff6ff",
            outline="",
        )
        self._canvas.create_line(
            self.X_PADDING,
            self.AXIS_Y,
            self.WIDTH - self.X_PADDING,
            self.AXIS_Y,
            fill="#6b7280",
            width=2,
        )
        for value in range(11):
            x = self._value_to_x(float(value))
            self._canvas.create_line(
                x, self.AXIS_Y - 5, x, self.AXIS_Y + 5, fill="#6b7280"
            )
            self._canvas.create_text(
                x,
                96,
                text=str(value),
                fill="#4b5563",
                font=("맑은 고딕", 7),
            )

    def _draw_target_marker(self, x: float) -> None:
        self._draw_triangle(x, (19, 19, 28), "#dc2626", "target_marker")
        self._canvas.create_line(
            x,
            29,
            x,
            self.AXIS_Y - 5,
            fill="#dc2626",
            width=3,
            tags="target_marker",
        )

    def _draw_current_marker(self, x: float) -> None:
        self._canvas.create_line(
            x,
            self.AXIS_Y + 5,
            x,
            68,
            fill="#2563eb",
            width=3,
            tags="current_marker",
        )
        self._draw_triangle(x, (80, 80, 71), "#2563eb", "current_marker")

    def _draw_overlap_marker(self, x: float) -> None:
        self._draw_triangle(x, (19, 19, 28), "#7e22ce", "overlap_marker")
        self._canvas.create_line(
            x, 36, x, 60, fill="#7e22ce", width=4, tags="overlap_marker"
        )
        self._draw_triangle(x, (80, 80, 71), "#7e22ce", "overlap_marker")

    def _draw_triangle(
        self,
        x: float,
        y_values: tuple[int, int, int],
        color: str,
        tag: str,
    ) -> None:
        self._canvas.create_polygon(
            x - 6,
            y_values[0],
            x + 6,
            y_values[1],
            x,
            y_values[2],
            fill=color,
            outline="",
            tags=tag,
        )
