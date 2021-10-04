import unittest
from epcore.ivmeasurer import IVMeasurerVirtualBad


class VirtualBadText(unittest.TestCase):
    def test_raises(self):
        bad = IVMeasurerVirtualBad(fail_chance=0.3, defer_open=True)
        success = False
        while not success:  # Open device
            try:
                bad.open_device()
                success = True
            except RuntimeError:
                bad.reconnect()
                continue

        successes = 0
        for _ in range(20):
            try:
                bad.get_settings()
                successes += 1
            except RuntimeError:
                if successes == 0:  # First call failed? Try to reconnect...
                    while not bad.reconnect():
                        pass
                    continue
                break  # Ok we already understand that sometimes it fails
        # Check that sometimes it fails
        self.assertTrue(0 < successes < 20)
