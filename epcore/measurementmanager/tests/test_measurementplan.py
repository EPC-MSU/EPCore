import unittest
from typing import List
from epcore.analogmultiplexer import AnalogMultiplexerVirtual
from epcore.elements import Board, Element, MultiplexerOutput, Pin
from epcore.ivmeasurer import IVMeasurerVirtual
from epcore.measurementmanager import MeasurementPlan


class TestPlan(unittest.TestCase):

    def setUp(self) -> None:
        self._measurer: IVMeasurerVirtual = IVMeasurerVirtual()
        self._empty_plan: MeasurementPlan = MeasurementPlan(board=Board(elements=[]), measurer=self._measurer)

        self._pins: List[Pin] = [Pin(x=i, y=i, measurements=[]) for i in range(5)]
        board: Board = Board(elements=[Element(pins=self._pins)])
        self._plan: MeasurementPlan = MeasurementPlan(board=board, measurer=self._measurer)

    def test_append_pin(self) -> None:
        self.assertEqual(self._empty_plan.pins_number, 0)
        self.assertIsNone(self._empty_plan.get_current_index())
        self.assertIsNone(self._empty_plan.get_current_pin())

        for i in range(6):
            new_pin_for_empty = Pin(x=i, y=i)
            self._empty_plan.append_pin(new_pin_for_empty)
            self.assertEqual(self._empty_plan.pins_number, i + 1)
            self.assertEqual(self._empty_plan.get_current_index(), i)
            self.assertEqual(self._empty_plan.get_current_pin(), new_pin_for_empty)

        self.assertEqual(self._plan.pins_number, 5)
        self.assertEqual(self._plan.get_current_index(), 0)
        self.assertEqual(self._plan.get_current_pin(), self._pins[0])

        new_pin_1 = Pin(x=6, y=6)
        self._plan.append_pin(new_pin_1)
        self.assertEqual(self._plan.pins_number, 6)
        self.assertEqual(self._plan.get_current_index(), 1)
        self.assertEqual(self._plan.get_current_pin(), new_pin_1)
        self.assertEqual(self._pins[1], new_pin_1)

        new_pin_2 = Pin(x=7, y=7)
        self._plan.go_pin(3)
        self._plan.append_pin(new_pin_2)
        self.assertEqual(self._plan.pins_number, 7)
        self.assertEqual(self._plan.get_current_index(), 4)
        self.assertEqual(self._plan.get_current_pin(), new_pin_2)
        self.assertEqual(self._pins[4], new_pin_2)

        new_pin_3 = Pin(x=8, y=8)
        self._plan.go_pin(6)
        self._plan.append_pin(new_pin_3)
        self.assertEqual(self._plan.pins_number, 8)
        self.assertEqual(self._plan.get_current_index(), 7)
        self.assertEqual(self._plan.get_current_pin(), new_pin_3)
        self.assertEqual(self._pins[7], new_pin_3)

    def test_get_current_index(self) -> None:
        self.assertIsNone(self._empty_plan.get_current_index())
        self.assertEqual(self._plan.get_current_index(), 0)

    def test_get_current_pin(self) -> None:
        self.assertIsNone(self._empty_plan.get_current_pin())
        self.assertEqual(self._plan.get_current_pin(), self._pins[0])

    def test_get_pin_with_index(self) -> None:
        self.assertIsNone(self._empty_plan.get_pin_with_index(0))
        self.assertIsNone(self._empty_plan.get_pin_with_index(67))

        for i, pin in enumerate(self._pins):
            self.assertEqual(self._plan.get_pin_with_index(i), pin)
        self.assertIsNone(self._plan.get_pin_with_index(len(self._pins)))

    def test_get_pins_without_multiplexer_outputs(self) -> None:
        self.assertEqual(self._empty_plan.get_pins_without_multiplexer_outputs(), [])
        self.assertEqual(self._plan.get_pins_without_multiplexer_outputs(), list(range(5)))

        pins = [Pin(x=0, y=0),
                Pin(x=1, y=1, multiplexer_output=MultiplexerOutput(channel_number=3, module_number=2)),
                Pin(x=2, y=2, multiplexer_output=MultiplexerOutput(channel_number=6, module_number=5)),
                Pin(x=3, y=3, multiplexer_output=MultiplexerOutput(channel_number=3, module_number=1)),
                Pin(x=4, y=4)]
        plan = MeasurementPlan(board=Board(elements=[Element(pins=pins)]), measurer=IVMeasurerVirtual(),
                               multiplexer=AnalogMultiplexerVirtual())
        self.assertEqual(plan.get_pins_without_multiplexer_outputs(), [0, 2, 4])

    def test_go_next_pin(self) -> None:
        for _ in range(5):
            self._empty_plan.go_next_pin()
            self.assertIsNone(self._empty_plan.get_current_index())
            self.assertIsNone(self._empty_plan.get_current_pin())

        for i in range(30):
            self._plan.go_next_pin()
            index = (i + 1) % 5
            self.assertEqual(self._plan.get_current_index(), index)
            self.assertEqual(self._plan.get_current_pin(), self._pins[index])

    def test_go_pin(self) -> None:
        for i in range(10):
            with self.assertRaises(ValueError):
                self._empty_plan.go_pin(i)

        for i in range(5):
            self._plan.go_pin(i)
            self.assertEqual(self._plan.get_current_pin(), self._pins[i])

        for i in range(5, 10):
            with self.assertRaises(ValueError):
                self._plan.go_pin(i)

    def test_go_prev_pin(self) -> None:
        for _ in range(5):
            self._empty_plan.go_prev_pin()
            self.assertIsNone(self._empty_plan.get_current_index())
            self.assertIsNone(self._empty_plan.get_current_pin())

        i = 0
        for _ in range(30):
            i = len(self._pins) - 1 if i <= 0 else i - 1
            self._plan.go_prev_pin()
            self.assertEqual(self._plan.get_current_index(), i)
            self.assertEqual(self._plan.get_current_pin(), self._pins[i])

    def test_remove_current_pin(self) -> None:
        self._empty_plan.remove_current_pin()
        self.assertIsNone(self._empty_plan.get_current_index())
        self.assertIsNone(self._empty_plan.get_current_pin())

        self.assertEqual(self._plan.pins_number, 5)

        self._plan.remove_current_pin()
        self.assertEqual(self._plan.pins_number, 4)
        self.assertEqual(self._plan.get_current_index(), 0)
        self.assertEqual(self._plan.get_current_pin(), self._pins[0])

        self._plan.go_pin(1)
        self._plan.remove_current_pin()
        self.assertEqual(self._plan.pins_number, 3)
        self.assertEqual(self._plan.get_current_index(), 1)
        self.assertEqual(self._plan.get_current_pin(), self._pins[1])

        self._plan.go_pin(2)
        self._plan.remove_current_pin()
        self.assertEqual(self._plan.pins_number, 2)
        self.assertEqual(self._plan.get_current_index(), 1)
        self.assertEqual(self._plan.get_current_pin(), self._pins[1])

        self._plan.go_pin(1)
        for i in (0, None):
            self._plan.remove_current_pin()
            self.assertEqual(self._plan.get_current_index(), i)
        self.assertEqual(self._plan.pins_number, 0)

    def test_save_comment_to_pin_with_index(self) -> None:
        for i in range(5):
            with self.assertRaises(IndexError):
                self._empty_plan.save_comment_to_pin_with_index(i, f"comment {i}")

        for i in range(self._plan.pins_number):
            comment = f"comment {i}"
            self._plan.save_comment_to_pin_with_index(i, comment)
            self.assertEqual(self._plan.get_pin_with_index(i).comment, comment)

        for i in range(20, 30):
            with self.assertRaises(IndexError):
                self._plan.save_comment_to_pin_with_index(i, f"comment {i}")

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
