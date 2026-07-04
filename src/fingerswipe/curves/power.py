import math

from fingerswipe.curves.base import Curve


class PowerCurve(Curve):

    def __init__(self, exponent: float = 2.0) -> None:
        self._exponent = exponent

    def transform(self, value: float) -> float:
        return math.copysign(abs(value) ** self._exponent, value)