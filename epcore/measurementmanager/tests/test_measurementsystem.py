import unittest

from copy import deepcopy

from epcore.measurementmanager import MeasurementSystem
from epcore.ivmeasurer import IVMeasurerVirtual
from epcore.elements import MeasurementSettings


class TestMeasurementSystem(unittest.TestCase):
    def test_all_settings_ok(self):
        iv1 = IVMeasurerVirtual()
        iv2 = IVMeasurerVirtual()
        iv3 = IVMeasurerVirtual()
        settings = MeasurementSettings(0, 1, 2, 3, 4)

        system = MeasurementSystem([iv1, iv2, iv3])

        system.set_settings(settings)

        self.assertTrue(system.get_settings() == settings)

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