import unittest
from epcore.ivmeasurer import IVMeasurerVirtual


class TestVirtualIVC(unittest.TestCase):
    def test_different_freqs(self):
        measurer = IVMeasurerVirtual()

        # just a few measurements
        for _ in range(100):
            measurer.measure_iv_curve()

        self.assertTrue(True)
