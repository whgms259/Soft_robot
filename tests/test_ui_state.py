"""단일 가변 휠 UI 상태 모델 시험."""

import unittest

from src.ui.models import (
    AdjustmentDirection,
    DriveDirection,
    WINDING_MAX,
    WINDING_MIN,
    WINDING_SPEED_MAX,
    WINDING_SPEED_MIN,
    WindingGaugeState,
    WheelUiState,
    clamp_winding_speed,
)


class WheelUiStateTests(unittest.TestCase):
    def test_safe_initial_state(self) -> None:
        state = WheelUiState()

        self.assertFalse(state.drive_enabled)
        self.assertEqual(state.drive_direction, DriveDirection.FORWARD)
        self.assertFalse(state.adjustment_enabled)
        self.assertEqual(state.adjustment_direction, AdjustmentDirection.UNWIND)

    def test_status_lines_reflect_all_four_controls(self) -> None:
        state = WheelUiState(
            drive_enabled=True,
            drive_direction=DriveDirection.REVERSE,
            adjustment_enabled=True,
            adjustment_direction=AdjustmentDirection.WIND,
        )

        self.assertEqual(
            state.status_lines(),
            (
                "주행 모터: ON",
                "주행 방향: -",
                "조절 모터: ON",
                "조절 방향: 감기",
            ),
        )


class WindingGaugeStateTests(unittest.TestCase):
    def test_initial_position_is_safe_minimum_without_target(self) -> None:
        state = WindingGaugeState()

        self.assertEqual(state.current, WINDING_MIN)
        self.assertIsNone(state.target)

    def test_target_is_clamped_to_reachable_range(self) -> None:
        state = WindingGaugeState()

        self.assertEqual(state.with_target(-1).target, WINDING_MIN)
        self.assertEqual(state.with_target(11).target, WINDING_MAX)

    def test_manual_movement_uses_point_one_per_second(self) -> None:
        state = WindingGaugeState(current=5.0)

        wound = state.advance_manual(AdjustmentDirection.WIND, 2.0)
        unwound = state.advance_manual(AdjustmentDirection.UNWIND, 2.0)

        self.assertAlmostEqual(wound.current, 5.2)
        self.assertAlmostEqual(unwound.current, 4.8)

    def test_manual_movement_stops_at_limits(self) -> None:
        state = WindingGaugeState(current=5.0)

        wound = state.advance_manual(AdjustmentDirection.WIND, 100.0)
        unwound = state.advance_manual(AdjustmentDirection.UNWIND, 100.0)

        self.assertEqual(wound.current, WINDING_MAX)
        self.assertEqual(unwound.current, WINDING_MIN)

    def test_target_movement_does_not_overshoot(self) -> None:
        state = WindingGaugeState(current=4.98, target=5.0)

        result = state.advance_toward_target(1.0)

        self.assertEqual(result.current, 5.0)
        self.assertTrue(result.is_at_target)

    def test_selected_speed_controls_manual_movement(self) -> None:
        state = WindingGaugeState(current=5.0)

        result = state.advance_manual(AdjustmentDirection.WIND, 2.0, speed=0.5)

        self.assertAlmostEqual(result.current, 6.0)

    def test_selected_speed_controls_target_movement(self) -> None:
        state = WindingGaugeState(current=5.0, target=7.0)

        result = state.advance_toward_target(2.0, speed=0.5)

        self.assertAlmostEqual(result.current, 6.0)

    def test_speed_is_clamped_and_rounded_to_one_decimal_place(self) -> None:
        self.assertEqual(clamp_winding_speed(0.0), WINDING_SPEED_MIN)
        self.assertEqual(clamp_winding_speed(1.1), WINDING_SPEED_MAX)
        self.assertEqual(clamp_winding_speed(0.30000000000000004), 0.3)


if __name__ == "__main__":
    unittest.main()
