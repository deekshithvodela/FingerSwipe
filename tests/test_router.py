import pytest
from fingerswipe.controllers.base import Controller
from fingerswipe.controllers.router import GestureAxisRouter
from fingerswipe.engine.motion import ProcessedMotion
from fingerswipe.interactions.phase import GesturePhase


class MockController(Controller):
    def __init__(self) -> None:
        self.handled_motions: list[ProcessedMotion] = []

    def handle(self, motion: ProcessedMotion) -> None:
        self.handled_motions.append(motion)


def test_router_locks_vertical_swipe_to_volume_controller() -> None:
    volume_ctrl = MockController()
    brightness_ctrl = MockController()
    router = GestureAxisRouter(vertical_controller=volume_ctrl, horizontal_controller=brightness_ctrl, axis_lock_threshold=2.0)

    # BEGIN phase dispatched to both controllers
    router.handle(ProcessedMotion(GesturePhase.BEGIN, 0.0, 0.0))
    assert router.mode == "UNLOCKED"
    assert len(volume_ctrl.handled_motions) == 1
    assert len(brightness_ctrl.handled_motions) == 1

    # Vertical motion below threshold (acc_y = -1.0)
    router.handle(ProcessedMotion(GesturePhase.UPDATE, 0.1, -1.0))
    assert router.mode == "UNLOCKED"

    # Cross lock threshold with strong vertical motion (acc_y = -3.0, acc_x = 0.2)
    router.handle(ProcessedMotion(GesturePhase.UPDATE, 0.1, -2.0))
    assert router.mode == "VERTICAL"
    # Verify initial accumulated motion was carried over to volume controller
    assert volume_ctrl.handled_motions[-1].dy == pytest.approx(-3.0)

    # Subsequent updates go ONLY to volume controller, even if dx is non-zero
    volume_count_before = len(volume_ctrl.handled_motions)
    brightness_count_before = len(brightness_ctrl.handled_motions)

    router.handle(ProcessedMotion(GesturePhase.UPDATE, 1.5, -2.0))
    assert len(volume_ctrl.handled_motions) == volume_count_before + 1
    assert len(brightness_ctrl.handled_motions) == brightness_count_before

    # END gesture resets router mode and notifies both controllers
    router.handle(ProcessedMotion(GesturePhase.END, 0.0, 0.0))
    assert router.mode == "UNLOCKED"


def test_router_locks_horizontal_swipe_to_brightness_controller() -> None:
    volume_ctrl = MockController()
    brightness_ctrl = MockController()
    router = GestureAxisRouter(vertical_controller=volume_ctrl, horizontal_controller=brightness_ctrl, axis_lock_threshold=2.0)

    router.handle(ProcessedMotion(GesturePhase.BEGIN, 0.0, 0.0))
    assert router.mode == "UNLOCKED"

    # Strong horizontal motion (dx = 2.5, dy = 0.1)
    router.handle(ProcessedMotion(GesturePhase.UPDATE, 2.5, 0.1))
    assert router.mode == "HORIZONTAL"
    # Verify initial accumulated dx was carried over to brightness controller
    assert brightness_ctrl.handled_motions[-1].dx == pytest.approx(2.5)

    volume_count_before = len(volume_ctrl.handled_motions)
    brightness_count_before = len(brightness_ctrl.handled_motions)

    # Subsequent updates go ONLY to brightness controller
    router.handle(ProcessedMotion(GesturePhase.UPDATE, 1.0, 1.0))
    assert len(brightness_ctrl.handled_motions) == brightness_count_before + 1
    assert len(volume_ctrl.handled_motions) == volume_count_before


def test_router_handles_single_enabled_axis() -> None:
    brightness_ctrl = MockController()
    # Volume disabled, vertical_controller is None
    router = GestureAxisRouter(vertical_controller=None, horizontal_controller=brightness_ctrl, axis_lock_threshold=0.5)

    router.handle(ProcessedMotion(GesturePhase.BEGIN, 0.0, 0.0))
    assert len(brightness_ctrl.handled_motions) == 1

    router.handle(ProcessedMotion(GesturePhase.UPDATE, 1.0, 0.0))
    assert router.mode == "HORIZONTAL"
    assert brightness_ctrl.handled_motions[-1].dx == pytest.approx(1.0)

    router.handle(ProcessedMotion(GesturePhase.END, 0.0, 0.0))
    assert router.mode == "UNLOCKED"


def test_router_4_finger_gestures_do_not_trigger_swipe_controllers() -> None:
    vol_ctrl = MockController()
    router = GestureAxisRouter(vertical_controller=vol_ctrl, axis_lock_threshold=0.5)

    router.handle(ProcessedMotion(GesturePhase.BEGIN, 0.0, 0.0, fingers=4))
    router.handle(ProcessedMotion(GesturePhase.UPDATE, 0.0, 5.0, fingers=4))
    router.handle(ProcessedMotion(GesturePhase.END, 0.0, 0.0, fingers=4))

    # 4-finger gestures must never trigger 3-finger volume swipe controller
    assert len(vol_ctrl.handled_motions) == 0





