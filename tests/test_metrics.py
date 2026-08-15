import numpy as np
import pytest

from mouse_ar.metrics import stationary_jitter


def test_identical_points_have_zero_jitter():
    points = [(10.0, 10.0)] * 10
    rms, p95, max_exc = stationary_jitter(points)
    assert rms == 0.0
    assert p95 == 0.0
    assert max_exc == 0.0


def test_rms_and_max_excursion_are_hand_computable():
    # points [(0,0),(2,0),(0,0)]; mean=(2/3,0)
    # distances: 2/3, 4/3, 2/3 -> rms = sqrt(((4/9)+(16/9)+(4/9))/3) = sqrt(8/9)
    # max excursion = 4/3; p95 (linear interp of sorted [2/3,2/3,4/3]) = 1.2666...
    points = [(0.0, 0.0), (2.0, 0.0), (0.0, 0.0)]

    rms, p95, max_exc = stationary_jitter(points)

    assert rms == pytest.approx(np.sqrt(8 / 9), abs=1e-6)
    assert max_exc == pytest.approx(4 / 3, abs=1e-6)
    assert p95 == pytest.approx(1.266666666, abs=1e-3)


def test_single_point_does_not_crash():
    rms, p95, max_exc = stationary_jitter([(3.0, 4.0)])
    assert rms == 0.0
    assert max_exc == 0.0
