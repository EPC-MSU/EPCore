import unittest

from epcore.ivmeasurer import IVMeasurerVirtualBad


class VirtualBadText(unittest.TestCase):
    def test_raises(self):
        bad = IVMeasurerVirtualBad(fail_chance=0.3)

        success = 0
        for c in range(100):
            try:
                bad.get_settings()
                success += 1
            except RuntimeError:
                bad.reconnect()
        # Check that sometimes it fails
        self.assertTrue(0 < success < 100)
