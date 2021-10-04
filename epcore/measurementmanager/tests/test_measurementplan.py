import unittest
from epcore.elements import Board, Element, Pin
from epcore.ivmeasurer import IVMeasurerVirtual
from epcore.measurementmanager import MeasurementPlan


class TestPlan(unittest.TestCase):

    def test_plan(self):
        pins = [Pin(0, 0, []), Pin(1, 1, [])]
        board = Board(elements=[Element(pins=pins)])
        measurer = IVMeasurerVirtual()

        plan = MeasurementPlan(board=board, measurer=measurer)

        # Check that first pin is first pin on board
        self.assertTrue(plan.get_current_pin() == pins[0])

        plan.go_next_pin()

        # Check that second pin is second pin on board
        self.assertTrue(plan.get_current_pin() == pins[1])

        # Trigger measure
        measurer.measure_iv_curve()
        # Save last measure
        plan.save_last_measurement_as_reference()

        # Check that after measurement current pin has reference IVC
        self.assertTrue(len(plan.get_current_pin().measurements) == 1)

        # Add new pin
        plan.append_pin(Pin(5, 5, measurements=[]))

        # Check that here are 3 pins
        self.assertTrue(len(plan.elements[0].pins) == 3)
