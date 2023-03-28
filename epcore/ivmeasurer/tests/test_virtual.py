import unittest
from time import sleep
from epcore.elements import MeasurementSettings
from epcore.ivmeasurer import IVMeasurerVirtual


class TestVirtualIVC(unittest.TestCase):

    def test_cache(self) -> None:
        measurer = IVMeasurerVirtual()
        with self.assertRaises(RuntimeError):
            measurer.get_last_iv_curve()  # measurement is not ready

        for _ in range(3):
            measured = measurer.measure_iv_curve()
            cached = measurer.get_last_cached_iv_curve()
            self.assertTrue(measured == cached)

    def test_freeze(self) -> None:
        measurer = IVMeasurerVirtual()
        # Read one curve and store to cash
        measurer.measure_iv_curve()
        measurer.freeze()
        measurer.trigger_measurement()
        sleep(2)
        self.assertFalse(measurer.measurement_is_ready())
        # Cached curve must be alive in freeze mode
        curve = measurer.get_last_cached_iv_curve()
        self.assertTrue(curve)

        measurer.unfreeze()
        measurer.trigger_measurement()
        sleep(2)
        # Measurement must be ready because we are not in freeze mode
        self.assertTrue(measurer.measurement_is_ready())

    def test_measurement(self) -> None:
        measurer = IVMeasurerVirtual()
        # Do a few measurements
        for _ in range(100):
            measurer.measure_iv_curve()
        self.assertTrue(True)

    def test_open_device(self) -> None:
        measurer = IVMeasurerVirtual(defer_open=True)
        with self.assertRaises(RuntimeError):
            measurer.calibrate()  # device closed, it must not work!
        measurer.open_device()
        measurer.calibrate()  # now it must work fine
        self.assertTrue(True)

    def test_set_settings(self) -> None:
        measurer = IVMeasurerVirtual()
        settings = MeasurementSettings(sampling_rate=300,
                                       internal_resistance=56,
                                       max_voltage=3.3,
                                       probe_signal_frequency=3,
                                       precharge_delay=None)
        measurer.set_settings(settings)
        settings_from_device = measurer.get_settings()
        self.assertEqual(settings, settings_from_device)
