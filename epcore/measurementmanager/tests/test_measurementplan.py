import unittest
from epcore.analogmultiplexer import AnalogMultiplexerVirtual
from epcore.elements import Board, Element, MultiplexerOutput, Pin
from epcore.ivmeasurer import IVMeasurerVirtual
from epcore.measurementmanager import MeasurementPlan


class TestPlan(unittest.TestCase):

    def test_plan(self):
        pins = [Pin(x=0, y=0, measurements=[]), Pin(x=1, y=1, measurements=[])]
        board = Board(elements=[Element(pins=pins)])
        measurer = IVMeasurerVirtual()
        plan = MeasurementPlan(board=board, measurer=measurer)

        # Check that first pin is first pin on board
        self.assertTrue(plan.get_current_pin() == pins[0])
        # Check that second pin is second pin on board
        plan.go_next_pin()
        self.assertTrue(plan.get_current_pin() == pins[1])
        # Trigger measure and save it as reference
        measurer.measure_iv_curve()
        plan.save_last_measurement_as_reference()
        # Check that current pin has one measurement and this measurement is reference IVC
        self.assertTrue(len(plan.get_current_pin().measurements) == 1)
        self.assertTrue(plan.get_current_pin().measurements[0].is_reference)
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
