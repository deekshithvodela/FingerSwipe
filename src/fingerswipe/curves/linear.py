from fingerswipe.curves.base import Curve


class LinearCurve(Curve):

    def transform(self, value: float) -> float:
        return value