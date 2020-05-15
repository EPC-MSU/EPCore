from ..elements import Board, Pin, Measurement, Element
from ..ivmeasurer import IVMeasurerBase

from copy import deepcopy


class MeasurementPlan(Board):
    """
    Measurement plan (test plan) – it is a linear series of measurements.
    It is a simple state machine.
    All board points should be aggregated in a series.
    This series is virtual and it is not stored anywhere.
    But for every point (except the first and the last)
    there is a single next point and a single previous point.
    The initial board structure should be saved.
    """
    def __init__(self, board: Board, measurer: IVMeasurerBase):
        super(MeasurementPlan, self).__init__(elements=board.elements)

        self._original_elements = deepcopy(board.elements)

        self.measurer = measurer
        self._all_pins = []
        for element in self.elements:
            for pin in element.pins:
                self._all_pins.append(pin)

        self._current_pin_index = 0

    def get_current_index(self) -> int:
        return self._current_pin_index

    def get_current_pin(self) -> Pin:
        return self._all_pins[self._current_pin_index]

    def append_pin(self, pin: Pin):
        self._all_pins.append(pin)
        if not self.elements:
            self.elements.append(Element(pins=[]))
        self.elements[-1].pins.append(pin)

    def go_next_pin(self):
        self._current_pin_index += 1
        if self._current_pin_index >= len(self._all_pins):
            self._current_pin_index = 0

    def go_prev_pin(self):
        self._current_pin_index -= 1
        if self._current_pin_index < 0:
            self._current_pin_index = len(self._all_pins) - 1

    def go_pin(self, pin_number: int):
        if pin_number >= len(self._all_pins) or pin_number < 0:
            raise ValueError(f"Pin {pin_number} does not exists")
        self._current_pin_index = pin_number

    def save_last_measurement_as_reference(self):
        """
        Turn last measurement for current pin
        to a reference measurement.
        """
        curve = self.measurer.get_last_iv_curve()
        settings = self.measurer.get_settings()
        measurement = Measurement(settings=settings, ivc=curve, is_reference=True)
        pin = self.get_current_pin()
        if not pin.measurements:
            pin.measurements.append(measurement)
        else:
            # TODO: zero? Reference measure is always zero index?
            pin.measurements[0] = measurement

    def restore_original_board(self):
        """
        Remove all changes in board like: adding new pins, measures, etc
        :return:
        """
        self.elements = deepcopy(self._original_elements)
