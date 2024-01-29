import unittest
from epcore.elements import MeasurementSettings
from epcore.ivmeasurer import IVMeasurerVirtual
from epcore.measurementmanager import Searcher
from epcore.product import EyePointProduct


class TestPlan(unittest.TestCase):

    def test_optimal_settings_search_settings_returned(self):
        measurer = IVMeasurerVirtual()
        test_settings = MeasurementSettings(
            sampling_rate=10000,
            probe_signal_frequency=100,
            internal_resistance=475,
            max_voltage=5.0
        )
        measurer.set_settings(test_settings)
        searcher = Searcher(measurer, EyePointProduct().get_parameters())
        searcher.search_optimal_settings()
        settings_after_search = measurer.get_settings()
        # The measurer should have initial settings after search
        self.assertTrue(settings_after_search is test_settings)

    def test_optimal_settings_set_new_settings(self):
        measurer = IVMeasurerVirtual()
        test_settings = MeasurementSettings(
            sampling_rate=100000,
            probe_signal_frequency=1000,
            internal_resistance=47500,
            max_voltage=12.0
        )
        measurer.set_settings(test_settings)
        searcher = Searcher(measurer, EyePointProduct().get_parameters())
        optimal_settings = searcher.search_optimal_settings()
        measurer.set_settings(optimal_settings)
        settings_after_search = measurer.get_settings()
        # The measurer should have new settings set
        self.assertTrue(settings_after_search is optimal_settings)  # TODO: "is" is just a pointer

    def test_optimal_settings_resistor(self):
        measurer = IVMeasurerVirtual()
        measurer.model = "resistor"
        measurer.nominal = 1000
        measurer.noise_factor = 0
        searcher = Searcher(measurer, EyePointProduct().get_parameters())
        optimal_settings = searcher.search_optimal_settings()
        good_settings = MeasurementSettings(
            sampling_rate=100000,
            internal_resistance=475.0,
            max_voltage=3.3,
            probe_signal_frequency=1000
        )
        # The measurer should have chosen good settings
        self.assertTrue(optimal_settings.sampling_rate == good_settings.sampling_rate)
        self.assertTrue(optimal_settings.internal_resistance == good_settings.internal_resistance)
        self.assertTrue(optimal_settings.max_voltage == good_settings.max_voltage)
        self.assertTrue(optimal_settings.probe_signal_frequency == good_settings.probe_signal_frequency)

    def test_optimal_settings_capacitor(self):
        measurer = IVMeasurerVirtual()
        measurer.model = "capacitor"
        measurer.nominal = 0.00001
        measurer.noise_factor = 0
        searcher = Searcher(measurer, EyePointProduct().get_parameters())
        optimal_settings = searcher.search_optimal_settings()
        good_settings = MeasurementSettings(
            sampling_rate=1000,
            internal_resistance=475.0,
            max_voltage=1.2,
            probe_signal_frequency=10
        )
        # The measurer should have good settings
        self.assertTrue(optimal_settings.sampling_rate == good_settings.sampling_rate)
        self.assertTrue(optimal_settings.internal_resistance == good_settings.internal_resistance)
        self.assertTrue(optimal_settings.max_voltage == good_settings.max_voltage)
        self.assertTrue(optimal_settings.probe_signal_frequency == good_settings.probe_signal_frequency)
