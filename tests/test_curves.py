import pytest

from fingerswipe.curves.exponential import ExponentialCurve
from fingerswipe.curves.linear import LinearCurve
from fingerswipe.curves.power import PowerCurve


@pytest.mark.parametrize("curve", [LinearCurve(), PowerCurve(), ExponentialCurve()])
def test_curves_preserve_sign_origin_and_unit_bounds(curve: object) -> None:
    transform = curve.transform  # type: ignore[attr-defined]
    assert transform(0.0) == 0.0
    assert transform(1.0) == pytest.approx(1.0)
    assert transform(-1.0) == pytest.approx(-1.0)
    assert transform(-0.5) < 0 < transform(0.5)
