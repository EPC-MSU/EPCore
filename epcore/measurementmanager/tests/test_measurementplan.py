import unittest
from epcore.analogmultiplexer import AnalogMultiplexerVirtual
from epcore.elements import Board, Element, MultiplexerOutput, Pin
from epcore.ivmeasurer import IVMeasurerVirtual
from epcore.measurementmanager import MeasurementPlan


class TestPlan(unittest.TestCase):

    def setUp(self) -> None:
        self._pins = [Pin(x=0, y=0, measurements=[]), Pin(x=1, y=1, measurements=[])]
        board = Board(elements=[Element(pins=self._pins)])
        self._measurer = IVMeasurerVirtual()
        self._plan = MeasurementPlan(board=board, measurer=self._measurer)

    def test_append_pin(self) -> None:
        pin_1 = Pin(x=2, y=2)
        self._plan.append_pin(pin_1)
        self.assertEqual(self._plan.get_current_pin(), pin_1)
        self.assertEqual(self._plan.get_current_index(), 1)

        pin_2 = Pin(x=3, y=3)
        self._plan.go_pin(2)
        self._plan.append_pin(pin_2)
        self.assertEqual(self._plan.get_current_pin(), pin_2)
        self.assertEqual(self._plan.get_current_index(), 3)

    def test_get_current_index(self) -> None:
        self.assertEqual(self._plan.get_current_index(), 0)

    def test_get_current_pin(self) -> None:
        self.assertEqual(self._plan.get_current_pin(), self._pins[0])

    def test_get_pin_with_index(self) -> None:
        self.assertEqual(self._plan.get_pin_with_index(1), self._pins[1])
        self.assertIsNone(self._plan.get_pin_with_index(4))

    def test_go_next_pin(self) -> None:
        self._plan.go_next_pin()
        self.assertEqual(self._plan.get_current_pin(), self._pins[1])

        self._plan.go_next_pin()
        self.assertEqual(self._plan.get_current_index(), 0)

    def test_go_pin(self) -> None:
        self._plan.go_pin(1)
        self.assertEqual(self._plan.get_current_pin(), self._pins[1])

        with self.assertRaises(ValueError):
            self._plan.go_pin(5)

    def test_go_prev_pin(self) -> None:
        self._plan.go_prev_pin()
        self.assertEqual(self._plan.get_current_pin(), self._pins[1])

        self._plan.go_prev_pin()
        self.assertEqual(self._plan.get_current_index(), 0)

    def test_remove_current_pin(self) -> None:
        self.assertEqual(len(self._plan.elements[0].pins), 2)

        self._plan.remove_current_pin()
        self.assertEqual(self._plan.get_current_index(), 0)
        self.assertEqual(len(self._plan.elements[0].pins), 1)

        self._plan.remove_current_pin()
        self.assertEqual(self._plan.get_current_pin(), None)
        self.assertEqual(len(self._plan.elements[0].pins), 0)

    def test_save_comment_to_pin_with_index(self) -> None:
        index = 0
        self._plan.save_comment_to_pin_with_index(index, "comment 0")
        self.assertEqual(self._plan.get_pin_with_index(index).comment, "comment 0")

        index = 1
        self._plan.save_comment_to_pin_with_index(index, "comment 1")
        self.assertEqual(self._plan.get_pin_with_index(index).comment, "comment 1")

    def test_save_last_measurement_as_reference(self) -> None:
        self.assertEqual(len(self._plan.get_current_pin().measurements), 0)

        self._measurer.measure_iv_curve()
        self._plan.save_last_measurement_as_reference()
        self.assertEqual(len(self._plan.get_current_pin().measurements), 1)
        self.assertTrue(self._plan.get_current_pin().measurements[0].is_reference)

    def test_save_last_measurement_as_test(self) -> None:
        self.assertEqual(len(self._plan.get_current_pin().measurements), 0)

        self._measurer.measure_iv_curve()
        self._plan.save_last_measurement_as_test()
        self.assertEqual(len(self._plan.get_current_pin().measurements), 1)
        self.assertFalse(self._plan.get_current_pin().measurements[0].is_reference)

    def test_plan(self) -> None:
        pins = [Pin(x=0, y=0, measurements=[]), Pin(x=1, y=1, measurements=[])]
        board = Board(elements=[Element(pins=pins)])
        measurer = IVMeasurerVirtual()
        plan = MeasurementPlan(board=board, measurer=measurer)

        # Add new pin and check that there are 3 pins
        plan.append_pin(Pin(5, 5, measurements=[]))
        self.assertTrue(len(plan.elements[0].pins) == 3)
        # Trigger measure and save it as test
        measurer.measure_iv_curve()
        plan.save_last_measurement_as_test()
        # Check that current pin has one measurement and this measurement is reference IVC
        self.assertTrue(len(plan.get_current_pin().measurements) == 1)
        self.assertFalse(plan.get_current_pin().measurements[0].is_reference)

    def test_plan_with_multiplexer(self):
        pins = [Pin(x=0, y=0, measurements=[]),
                Pin(x=1, y=1, measurements=[], multiplexer_output=MultiplexerOutput(channel_number=3, module_number=2)),
                Pin(x=2, y=2, measurements=[], multiplexer_output=MultiplexerOutput(channel_number=6, module_number=5))]
        board = Board(elements=[Element(pins=pins)])
        measurer = IVMeasurerVirtual()
        multiplexer = AnalogMultiplexerVirtual()
        plan = MeasurementPlan(board=board, measurer=measurer, multiplexer=multiplexer)

        self.assertEqual(len(plan.elements[0].pins), 3)
        self.assertEqual(plan.get_pins_without_multiplexer_outputs(), [0, 2])
