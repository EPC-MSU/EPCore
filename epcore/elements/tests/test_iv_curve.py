import unittest
import numpy as np
from epcore.elements import IVCurve


class IVCurveTests(unittest.TestCase):

    def test_default_arrays(self) -> None:
        test_curve = IVCurve()
        self.assertTrue(len(test_curve.voltages))
        self.assertTrue(np.allclose(test_curve.voltages, [0, 0]))

    def test_incorrect_length(self) -> None:
        with self.assertRaises(ValueError):
            IVCurve(currents=[1], voltages=[1])

    def test_length_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            IVCurve(currents=[1, 2, 3], voltages=[1, 2])
