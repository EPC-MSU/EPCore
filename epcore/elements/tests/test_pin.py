import unittest
from epcore.elements import IVCurve, Measurement, MeasurementSettings, Pin


class TestPin(unittest.TestCase):

    def test_remove_all_test_signatures(self) -> None:
        """
        Test checks the removal of test signatures from pin measurements.
        """

        ref_measurement = Measurement(settings=MeasurementSettings(1, 2, 3, 4, 5),
                                      ivc=IVCurve([1, 2, 3], [1, 2, 3]), is_reference=True)
        measurements = [ref_measurement]
        for i in range(1, 10):
            test_measurement = Measurement(settings=MeasurementSettings(1, 2, 3, 4, 5),
                                           ivc=IVCurve([1 * i, 2 * i, 3 * i], [1 * i, 2 * i, 3 * i]))
            measurements.append(test_measurement)

        pin = Pin(0, 0, measurements=measurements)
        pin.remove_test_measurements()

        self.assertEqual(len(pin.measurements), 1)
        self.assertEqual(pin.get_reference_measurement(), ref_measurement)
