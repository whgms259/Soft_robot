"""가변 휠 시험 UI의 프로젝트 루트 실행 진입점."""

from __future__ import annotations

import sys
import tkinter as tk

from src.ui.control_panel import VariableWheelControlApp
from src.ui.models import (
    DRIVE_SPEED_DEFAULT,
    DRIVE_SPEED_MAX,
    DRIVE_SPEED_MIN,
    DRIVE_SPEED_STEP,
    GAUGE_DISPLAY_MAX,
    GAUGE_DISPLAY_MIN,
    UPDATE_INTERVAL_MS,
    WINDING_MAX,
    WINDING_MIN,
    WINDING_SPEED_MAX,
    WINDING_SPEED_MIN,
    WINDING_SPEED_STEP,
    AdjustmentDirection,
    DriveDirection,
    WheelUiState,
    WindingGaugeState,
)
from src.ui.widgets import ToggleSwitch, WindingGauge


__all__ = [
    "AdjustmentDirection",
    "DRIVE_SPEED_DEFAULT",
    "DRIVE_SPEED_MAX",
    "DRIVE_SPEED_MIN",
    "DRIVE_SPEED_STEP",
    "DriveDirection",
    "GAUGE_DISPLAY_MAX",
    "GAUGE_DISPLAY_MIN",
    "ToggleSwitch",
    "UPDATE_INTERVAL_MS",
    "VariableWheelControlApp",
    "WINDING_MAX",
    "WINDING_MIN",
    "WINDING_SPEED_MAX",
    "WINDING_SPEED_MIN",
    "WINDING_SPEED_STEP",
    "WheelUiState",
    "WindingGauge",
    "WindingGaugeState",
    "main",
]


def main() -> None:
    """UI application을 실행한다."""

    root = tk.Tk()
    root.title("가변 휠 기본 제어")
    root.geometry("720x760")
    root.minsize(680, 760)
    VariableWheelControlApp(root)
    root.mainloop()


if __name__ == "__main__":
    if sys.argv[1:] == ["--check"]:
        print("UI launcher import check: OK")
    else:
        main()
