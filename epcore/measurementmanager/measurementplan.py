from copy import deepcopy
from typing import Iterable, List, Optional, Tuple
from epcore.analogmultiplexer import AnalogMultiplexerBase
from epcore.elements import Board, Element, Measurement, Pin
from epcore.ivmeasurer import IVMeasurerBase


class MeasurementPlan(Board):
    """
    Measurement plan (test plan) – it is a linear series of measurements.
    It is a simple state machine. All board points should be aggregated
    in a series. This series is virtual and it is not stored anywhere.
    But for every point (except the first and the last) there is a single
    next point and a single previous point. The initial board structure
    should be saved.
    """

    def __init__(self, board: Board, measurer: IVMeasurerBase, multiplexer: Optional[AnalogMultiplexerBase] = None):
        """
        :param board: initial board;
        :param measurer: tested measurer;
        :param multiplexer: analog multiplexer.
        """

        super().__init__(elements=board.elements, image=board.image)
        self._original_elements = deepcopy(board.elements)
        self.measurer = measurer
        self.multiplexer = multiplexer
        self._all_pins = []
        for element in self.elements:
            for pin in element.pins:
                self._all_pins.append(pin)
        self._current_pin_index = 0

    def _save_last_measurement(self, is_reference: bool = True):
        """
        Method gets last measurement from measurer and saves it as
        reference or test measurement for current pin.
        :param is_reference: if True then measurement will be saved as reference.
        """

        curve = self.measurer.get_last_cached_iv_curve()
        settings = self.measurer.get_settings()
        measurement = Measurement(settings=deepcopy(settings), ivc=curve, is_reference=is_reference)
        pin = self.get_current_pin()
        if is_reference:
            pin.set_reference_measurement(measurement)
        else:
            pin.append_test_measurement(measurement)

    def all_pins_iterator(self) -> Iterable[Tuple[int, Pin]]:
        yield from enumerate(self._all_pins)

    def append_pin(self, pin: Pin):
        """
        Append new pin to measurement plan.
        :param pin: pin to append.
        """

        self._all_pins.append(pin)
        if not self.elements:
            self.elements.append(Element(pins=[]))
        self.elements[-1].pins.append(pin)
        self._current_pin_index = len(self._all_pins) - 1

    def get_current_index(self) -> int:
        """
        :return: index of current pin.
        """

        return self._current_pin_index

    def get_current_pin(self) -> Pin:
        """
        :return: current pin.
        """

        return self._all_pins[self._current_pin_index]

    def get_pins_without_multiplexer_outputs(self) -> List[int]:
        """
        Returns list of indexes of pins whose multiplexer output is None
        or output cannot be set using current multiplexer configuration.
        :return: list of indexes of pins.
        """

        indexes = []
        for index, pin in self._all_pins:
            if pin.multiplexer_output is None or\
                    (self.multiplexer and not self.multiplexer.is_correct_output(pin.multiplexer_output)):
                indexes.append(index)
        return indexes

    def go_next_pin(self):
        """
        Go to next pin.
        """

        self._current_pin_index += 1
        if self._current_pin_index >= len(self._all_pins):
            self._current_pin_index = 0

    def go_pin(self, pin_number: int):
        """
        Go to pin with given index.
        :param pin_number: index of required pin.
        """

        if pin_number >= len(self._all_pins) or pin_number < 0:
            raise ValueError(f"Pin {pin_number} does not exists")
        self._current_pin_index = pin_number

    def go_prev_pin(self):
        """
        Go to previous pin.
        """

        self._current_pin_index -= 1
        if self._current_pin_index < 0:
            self._current_pin_index = len(self._all_pins) - 1

    def restore_original_board(self):
        """
        Remove all changes in board like: adding new pins, measures, etc.
        """

        self.elements = deepcopy(self._original_elements)

    def save_last_measurement_as_reference(self):
        """
        Method gets last measurement from measurer and saves it as
        reference measurement for current pin.
        """

        self._save_last_measurement()

    def save_last_measurement_as_test(self):
        """
        Method gets last measurement from measurer and saves it as
        test measurement for current pin.
        """

        self._save_last_measurement(False)
