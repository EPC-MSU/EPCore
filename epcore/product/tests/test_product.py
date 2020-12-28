import unittest
from epcore.product import EPLab
from epcore.measurementmanager import MeasurementSystem
from epcore.ivmeasurer import IVMeasurerVirtual


class TestEPLabProduct(unittest.TestCase):
    def test_rw_settings(self):
        eplab = EPLab(MeasurementSystem([IVMeasurerVirtual(), IVMeasurerVirtual()]))

        options = {
            EPLab.Parameter.frequency: "100hz",
            EPLab.Parameter.sensitive: "middle",
            EPLab.Parameter.voltage: "3.3v"
        }

        eplab.set_settings_from_options(options)
        read_options = eplab.get_current_options()

        self.assertTrue(read_options == options)
