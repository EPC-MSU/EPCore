import unittest

from epcore.ivmeasurer import IVMeasurerVirtual
from epcore.elements import MeasurementSettings
from epcore.measurementmanager import search_optimal_settings


class TestPlan(unittest.TestCase):
    def test_optimal_settings_search_settings_returned(self):
        measurer = IVMeasurerVirtual()

        test_settings = MeasurementSettings(
            sampling_rate=10000,
            probe_signal_frequency=100,
            internal_resistance=475,
            max_voltage=5
        )
        measurer.set_settings(test_settings)

        search_optimal_settings(measurer)

        settings_after_search = measurer.get_settings()

        # The measurer should have initial settings after search
        self.assertTrue(settings_after_search is test_settings)
