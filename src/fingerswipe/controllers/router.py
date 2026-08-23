import logging
import time
from fingerswipe.controllers.base import Controller
from fingerswipe.engine.motion import ProcessedMotion
from fingerswipe.interactions.phase import GesturePhase


class GestureAxisRouter(Controller):

    def __init__(
        self,
        vertical_controller: Controller | None = None,
        horizontal_controller: Controller | None = None,
        axis_lock_threshold: float = 0.5,
    ) -> None:
        self._vertical_controller = vertical_controller
        self._horizontal_controller = horizontal_controller
        self._axis_lock_threshold = axis_lock_threshold
        self._logger = logging.getLogger("fingerswipe.router")

        self._mode = "UNLOCKED"
        self._acc_x = 0.0
        self._acc_y = 0.0
        self._start_time_ns = 0
        self._active_fingers = 3

    @property
    def mode(self) -> str:
        return self._mode

    def update_axis_lock_threshold(self, threshold: float) -> None:
        self._axis_lock_threshold = threshold

    def handle(self, motion: ProcessedMotion) -> None:
        if motion.phase is GesturePhase.BEGIN:
            self._mode = "UNLOCKED"
            self._acc_x = 0.0
            self._acc_y = 0.0
            self._start_time_ns = time.monotonic_ns()
            self._active_fingers = motion.fingers
            if self._active_fingers == 3:
                if self._vertical_controller:
                    self._vertical_controller.handle(motion)
                if self._horizontal_controller:
                    self._horizontal_controller.handle(motion)
            return

        if motion.phase in (GesturePhase.END, GesturePhase.CANCEL):
            if self._active_fingers == 3:
                if self._vertical_controller:
                    self._vertical_controller.handle(motion)
                if self._horizontal_controller:
                    self._horizontal_controller.handle(motion)
            self._mode = "UNLOCKED"
            self._acc_x = 0.0
            self._acc_y = 0.0
            self._start_time_ns = 0
            self._active_fingers = 3
            return

        if motion.phase is not GesturePhase.UPDATE:
            return

        # 4-finger gestures accumulate displacement for 4-finger swipe, but NEVER trigger 3-finger volume/brightness
        if self._active_fingers == 4:
            self._acc_x += motion.dx
            self._acc_y += motion.dy
            return

        # 3-finger gestures route to volume or brightness
        if self._mode == "UNLOCKED":
            self._acc_x += motion.dx
            self._acc_y += motion.dy

            abs_x = abs(self._acc_x)
            abs_y = abs(self._acc_y)
            dist = abs_x + abs_y

            lock_threshold = self._axis_lock_threshold

            if dist >= lock_threshold:
                if abs_y > abs_x:
                    self._mode = "VERTICAL"
                    if self._vertical_controller:
                        self._vertical_controller.handle(ProcessedMotion(GesturePhase.UPDATE, 0.0, self._acc_y, motion.fingers))
                else:
                    self._mode = "HORIZONTAL"
                    if self._horizontal_controller:
                        self._horizontal_controller.handle(ProcessedMotion(GesturePhase.UPDATE, self._acc_x, 0.0, motion.fingers))
            return

        if self._mode == "VERTICAL" and self._vertical_controller:
            self._vertical_controller.handle(motion)
        elif self._mode == "HORIZONTAL" and self._horizontal_controller:
            self._horizontal_controller.handle(motion)
