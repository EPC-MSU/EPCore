from ..elements import Board, Pin, Measurement
from ..ivmeasurer import IVMeasurerBase


class MeasurementPlan(Board):
    """
    Measurement plan (test plan) – it is a linear series of measurements.
    It is a simple state machiine.
    All board points should be aggregated in a series.
    This series is virtual and it is not stored anywhere.
    But for every point (except the first and the last)
    there is a single next point and a single previous point.
    The initial board structure should be saved.
    """
    def __init__(self, board: Board = Board()):
        self.measurer = IVMeasurerBase()

    def assign_measurer(self, measurer: IVMeasurerBase):
        self.measurer = measurer

    def get_current_pin(self) -> Pin:
        return Pin()

    def apppend_pin(self, pin: Pin):
        pass

    def load_next_pin(self):
        pass

    def load_prev_pin(self):
        pass

    def load_pin(self, pin_number: int):
        """
        Load pin by its number in global series.
        """
        pass

    def measure(self):
        """
        Make measurement for current pin.
        You can get the result
        by calling get_current_pin()
        """

    def assign_measurement(self, measurement: Measurement):
        """
        Assign measurement for current pin.
        """
        pass

    def save_last_measurement_as_reference(self):
        """
        Turn last measurement for current pin
        to a reference measurement.
        """

    def export_to_board(self) -> Board:
        return Board()
