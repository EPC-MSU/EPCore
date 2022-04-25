import unittest
from copy import deepcopy
from time import sleep
from epcore.analogmultiplexer import AnalogMultiplexerVirtual
from epcore.elements import MeasurementSettings, MultiplexerOutput
from epcore.ivmeasurer import IVMeasurerVirtual
from epcore.measurementmanager import MeasurementSystem


class TestMeasurementSystem(unittest.TestCase):

    def test_all_settings_ok(self):
        iv1 = IVMeasurerVirtual()
        iv2 = IVMeasurerVirtual()
        iv3 = IVMeasurerVirtual()
        settings = MeasurementSettings(0, 1, 2, 3, 4)
        system = MeasurementSystem([iv1, iv2, iv3])
        system.set_settings(settings)
        self.assertTrue(system.get_settings() == settings)

    def test_map(self):
        iv1 = IVMeasurerVirtual(name="foo")
        iv2 = IVMeasurerVirtual(name="bar")
        iv3 = IVMeasurerVirtual(name="spam")
        system = MeasurementSystem([iv1, iv2, iv3])
        self.assertTrue(system.measurers_map["foo"] is iv1)
        self.assertTrue(system.measurers_map["bar"] is iv2)
        self.assertTrue(system.measurers_map["spam"] is iv3)

    def test_raises(self):
        iv1 = IVMeasurerVirtual()
        iv2 = IVMeasurerVirtual()
        iv3 = IVMeasurerVirtual()
        settings = MeasurementSettings(0, 1, 2, 3, 4)
        iv1.set_settings(settings)
        iv2.set_settings(settings)
        settings2 = deepcopy(settings)
        settings2.max_voltage = 345
        iv3.set_settings(settings2)
        system = MeasurementSystem([iv1, iv2, iv3])
        with self.assertRaises(ValueError):
            system.get_settings()

    def test_measurements_ready(self):
        iv1 = IVMeasurerVirtual()
        iv2 = IVMeasurerVirtual()
        system = MeasurementSystem([iv1, iv2])
        system.trigger_measurements()
        sleep(2)
        # Test that after some time all measurements are ready
        self.assertTrue(system.measurements_are_ready())
        # Let's freeze one measurer
        iv1.freeze()
        system.trigger_measurements()
        sleep(2)
        # Test that freezed measurers are ignored
        self.assertTrue(system.measurements_are_ready())

    def test_multiplexers_are_in_system(self):
        """
        Test checks if there are multiplexers in measurement system.
        """

        multiplexer = AnalogMultiplexerVirtual()
        system_with_multiplexer = MeasurementSystem(multiplexers=[multiplexer])
        self.assertTrue(system_with_multiplexer.has_active_analog_multiplexers())
        system_without_multiplexer = MeasurementSystem()
        self.assertFalse(system_without_multiplexer.has_active_analog_multiplexers())

    def test_multiplexer_output(self):
        """
        Test checks that measurement system correctly sets output for
        all multiplexers.
        """

        output = MultiplexerOutput(channel_number=33, module_number=2)
        multiplexers = [AnalogMultiplexerVirtual() for _ in range(5)]
        system = MeasurementSystem(multiplexers=multiplexers)
        system.set_multiplexer_output(output)
        self.assertTrue(all([multiplexer.get_connected_channel() == output for multiplexer in multiplexers]))
