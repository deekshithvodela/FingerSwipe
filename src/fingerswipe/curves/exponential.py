import math

from fingerswipe.curves.base import Curve


class ExponentialCurve(Curve):

    def __init__(self, factor: float = 3.0) -> None:
        self._factor = factor

    def transform(self, value: float) -> float:
        if value == 0.0:
            return 0.0

        numerator = math.exp(self._factor * abs(value)) - 1.0
        denominator = math.exp(self._factor) - 1.0

        return math.copysign(numerator / denominator, value)