import numpy as np
from ..measurement import IVCurve


def test_default_arrays():
    test_curve = IVCurve()

    assert len(test_curve.voltages)
    assert np.allclose(test_curve.voltages, [0, 0])


def test_lehgth_mismatch():
    try:
        IVCurve(
            currents=[1, 2, 3],
            voltages=[1, 2]
        )

        # If we are here, no exception occurred,
        # but there should be ValueError
        assert 0
    except ValueError:
        pass


def test_incorrent_length():
    try:
        IVCurve(
            currents=[1],
            voltages=[1]
        )

        # If we are here, no exception occurred,
        # but there should be ValueError
        assert 0
    except ValueError:
        pass
