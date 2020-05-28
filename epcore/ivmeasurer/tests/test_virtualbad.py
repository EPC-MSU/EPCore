import unittest

from epcore.ivmeasurer import IVMeasurerVirtualBad


class VirtualBadText(unittest.TestCase):
    def test_raises(self):
        bad = IVMeasurerVirtualBad(fail_chance=0.3)

        successes = 0
        for c in range(20):
            try:
                bad.get_settings()
                successes += 1
            except RuntimeError:
                if successes == 0:  # First call failed? Try to reconnect...
                    bad.reconnect()
                    continue
                else:
                    break  # Ok we already understand that sometimes it fails
        # Check that sometimes it fails
        self.assertTrue(0 < successes < 100)
