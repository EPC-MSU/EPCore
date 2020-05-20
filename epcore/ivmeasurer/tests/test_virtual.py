import unittest
from epcore.ivmeasurer import IVMeasurerVirtual
from time import sleep


class TestVirtualIVC(unittest.TestCase):
    def test_measurement(self):
        measurer = IVMeasurerVirtual()

        # just a few measurements
        for _ in range(100):
            measurer.measure_iv_curve()

        self.assertTrue(True)

    def test_cache(self):
        measurer = IVMeasurerVirtual()

        with self.assertRaises(RuntimeError):
            measurer.get_last_iv_curve()  # measurement is not ready

        for _ in range(3):
            measured = measurer.measure_iv_curve()
            cached = measurer.get_last_cached_iv_curve()
            self.assertTrue(measured == cached)

        settings = measurer.get_settings()
        settings.probe_signal_frequency = 1  # Go slow mode
        settings.sampling_rate = 100
        measurer.set_settings(settings)

        measurer.trigger_measurement()
        # Last curve may not be ready...
        self.assertTrue(measurer.get_last_cached_iv_curve())
        # ...but the last measured curve must be alive

    def test_freeze(self):
        measurer = IVMeasurerVirtual()
        # Read one curve and store to cash
        measurer.measure_iv_curve()

        measurer.freeze()
        measurer.trigger_measurement()

        sleep(2)
        # Measurement must NOT be ready because measurer is in freeze mode
        self.assertTrue(not measurer.measurement_is_ready())

        # Cached curve must be alive in freeze mode
        curve = measurer.get_last_cached_iv_curve()
        self.assertTrue(curve)

        measurer.unfreeze()
        measurer.trigger_measurement()

        sleep(2)
        # Measurement must be ready because not we are not in freeze mode
        self.assertTrue(measurer.measurement_is_ready())
