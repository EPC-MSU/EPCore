from copy import deepcopy
from typing import Any, Callable, Iterable, List, Optional, Tuple
from epcore.analogmultiplexer import AnalogMultiplexerBase
from epcore.elements import Board, Element, Measurement, MultiplexerOutput, Pin
from epcore.ivmeasurer import IVMeasurerBase


def call_callback_funcs_for_pin_changes(func: Callable[..., Any]):
    """
    Decorator calls callback functions for case when pin parameters have changed.
    :param func: decorated function.
    """

    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        current_pin_index = self.get_current_index()
        for callback_func in self.callback_funcs_for_pin_changes:
            callback_func(current_pin_index)
        return result

    return wrapper


def set_current_pin_output_to_multiplexer(func: Callable[..., None]):
    """
    Decorator sets output of current pin to multiplexer and calls callback functions for case when multiplexer output
    have changed.
    :param func: decorated function.
    """

    def wrapper(self, *args, **kwargs) -> None:
        func(self, *args, **kwargs)
        pin = self.get_current_pin()
        if not self.multiplexer or not pin.multiplexer_output:
            return

        self.multiplexer.connect_channel(pin.multiplexer_output)
        for callback_func in self.callback_funcs_for_mux_output_change:
            callback_func(pin.multiplexer_output)

    return wrapper


class MeasurementPlan(Board):
    """
    Measurement plan (test plan) – it is a linear series of measurements. It is a simple state machine. All board points
    should be aggregated in a series. This series is virtual and it is not stored anywhere. But for every point (except
    the first and the last) there is a single next point and a single previous point. The initial board structure
    should be saved.
    """

    def __init__(self, board: Board, measurer: IVMeasurerBase, multiplexer: Optional[AnalogMultiplexerBase] = None
                 ) -> None:
        """
        :param board: initial board;
        :param measurer: tested measurer;
        :param multiplexer: analog multiplexer.
        """

        super().__init__(elements=board.elements, image=board.image)
        self._original_elements = deepcopy(board.elements)
        self.callback_funcs_for_mux_output_change: List[Callable] = []
        self.callback_funcs_for_pin_changes: List[Callable] = []
        self.measurer: IVMeasurerBase = measurer
        self.multiplexer: AnalogMultiplexerBase = multiplexer
        self._all_pins: List[Pin] = self._get_all_pins()
        self._current_pin_index: int = 0

    def _get_all_pins(self) -> List[Pin]:
        pins = []
        for element in self.elements:
            for pin in element.pins:
                pins.append(pin)
        return pins

    def _save_last_measurement(self, is_reference: bool = True, invalidate_test: bool = False) -> None:
        """
        Method gets last measurement from measurer and saves it as reference or test measurement for current pin.
        :param is_reference: if True then measurement will be saved as reference;
        :param invalidate_test: if True then test measurements will be removed from current pin.
        """

        curve = self.measurer.get_last_cached_iv_curve()
        settings = self.measurer.get_settings()
        measurement = Measurement(settings=deepcopy(settings), ivc=curve, is_reference=is_reference)
        pin = self.get_current_pin()
        if is_reference:
            pin.set_reference_measurement(measurement, invalidate_test)
        else:
            pin.set_test_measurement(measurement)

    def add_callback_func_for_mux_output_change(self, callback_func: Callable[MultiplexerOutput, None]) -> None:
        """
        Method adds new callback function that will be called when multiplexer output changes.
        :param callback_func: callback function to be added.
        """

        self.callback_funcs_for_mux_output_change.append(callback_func)

    def add_callback_func_for_pin_changes(self, callback_func: Callable[int, None]) -> None:
        """
        Method adds new callback function that will be called when pin changes.
        :param callback_func: callback function to be added.
        """

        self.callback_funcs_for_pin_changes.append(callback_func)

    def all_pins_iterator(self) -> Iterable[Tuple[int, Pin]]:
        yield from enumerate(self._all_pins)

    @call_callback_funcs_for_pin_changes
    def append_pin(self, pin: Pin) -> None:
        """
        Append new pin to measurement plan. The new pin is not added to the end, but immediately after the current one.
        :param pin: pin to append.
        """

        index = self._current_pin_index + 1
        append_item_to_list(self._all_pins, index, pin)

        if not self.elements:
            self.elements.append(Element(pins=[]))

        i = 0
        for element in self.elements:
            length = len(element.pins)
            if i <= self._current_pin_index <= i + length:
                index = self._current_pin_index - i + 1
                append_item_to_list(element.pins, index, pin)
                break
            i += length

        if len(self._all_pins) == 1:
            self._current_pin_index = 0
        else:
            self._current_pin_index += 1

    def get_current_index(self) -> int:
        """
        :return: index of current pin.
        """

        return self._current_pin_index

    def get_current_pin(self) -> Optional[Pin]:
        """
        :return: current pin.
        """

        return self.get_pin_with_index(self._current_pin_index)

    def get_pin_with_index(self, index: int) -> Optional[Pin]:
        """
        Method returns pin with given index.
        :param index: index of required pin.
        :return: pin.
        """

        try:
            return self._all_pins[index]
        except IndexError:
            return None

    def get_pins_without_multiplexer_outputs(self) -> List[int]:
        """
        Returns list of indexes of pins whose multiplexer output is None or output cannot be set using current
        multiplexer configuration.
        :return: list of indexes of pins.
        """

        indexes = []
        for index, pin in enumerate(self._all_pins):
            if pin.multiplexer_output is None or \
                    (self.multiplexer and not self.multiplexer.is_correct_output(pin.multiplexer_output)):
                indexes.append(index)
        return indexes

    @call_callback_funcs_for_pin_changes
    @set_current_pin_output_to_multiplexer
    def go_next_pin(self) -> None:
        """
        Go to next pin.
        """

        self._current_pin_index += 1
        if self._current_pin_index >= len(self._all_pins):
            self._current_pin_index = 0

    @call_callback_funcs_for_pin_changes
    @set_current_pin_output_to_multiplexer
    def go_pin(self, pin_number: int) -> None:
        """
        Go to pin with given index.
        :param pin_number: index of required pin.
        """

        if pin_number >= len(self._all_pins) or pin_number < 0:
            raise ValueError(f"Pin {pin_number} does not exist")
        self._current_pin_index = pin_number

    @call_callback_funcs_for_pin_changes
    @set_current_pin_output_to_multiplexer
    def go_prev_pin(self) -> None:
        """
        Go to previous pin.
        """

        self._current_pin_index -= 1
        if self._current_pin_index < 0:
            self._current_pin_index = len(self._all_pins) - 1
        if len(self._all_pins) == 0:
            self._current_pin_index = 0

    def remove_all_callback_funcs_for_mux_output_change(self) -> None:
        """
        Method removes all callback functions for multiplexer output changes.
        """

        self.callback_funcs_for_mux_output_change = []

    def remove_all_callback_funcs_for_pin_changes(self) -> None:
        """
        Method removes all callback functions for pin changes.
        """

        self.callback_funcs_for_pin_changes = []

    def restore_original_board(self) -> None:
        """
        Remove all changes in board like: adding new pins, measures, etc.
        """

        self.elements = deepcopy(self._original_elements)

    @call_callback_funcs_for_pin_changes
    def save_comment_to_pin_with_index(self, pin_index: int, comment: str) -> None:
        """
        Method saves comment to pin with given index.
        :param pin_index: index of pin;
        :param comment: comment for pin.
        """

        self._all_pins[pin_index].comment = comment

    @call_callback_funcs_for_pin_changes
    def save_last_measurement_as_reference(self, invalidate_test: bool = False) -> None:
        """
        Method gets last measurement from measurer and saves it as reference measurement for current pin.
        :param invalidate_test: if True then test measurements will be removed from current pin.
        """

        self._save_last_measurement(is_reference=True, invalidate_test=invalidate_test)

    @call_callback_funcs_for_pin_changes
    def save_last_measurement_as_test(self) -> None:
        """
        Method gets last measurement from measurer and saves it as test measurement for current pin.
        """

        self._save_last_measurement(is_reference=False)


def append_item_to_list(item_list: List[Any], index: int, item: Any) -> None:
    """
    :param item_list: list of elements;
    :param index: index in the list where to insert a new element;
    :param item: new element.
    """

    if index <= len(item_list) - 1:
        item_list.insert(index, item)
    else:
        item_list.append(item)
