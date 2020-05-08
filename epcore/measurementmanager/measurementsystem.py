from typing import List
import time
from ..elements import Measurement, MeasurementSettings, IVCurve
from ..ivmeasurer import IVMeasurerBase

class MeasurementSystem:
    """
    Provide mass operations with a number of IVMeasurers.
    If you have only single IVMeasurer, it is recommended to use
    this class for compatibility.

    """
    def __init__(self, measurers: List[IVMeasurerBase] = []):
        self.measurers = measurers

    def trigger_measurements(self):
        """
        Trigger measurements on all devices
        """
        for m in self.measurers:
            m.trigger_measurement()

    def measurements_are_ready(self) -> bool:
        """
        Return True if all measurers
        have done their Job
        """
        for m in self.measurers:
            if not m.measurement_is_ready():
                return False
        
        return True

    def measure_iv_curves(self) -> List[IVCurve]:
        """
        Make measurements and
        get new curves from all devices.
        """
        self.trigger_measurements()

        while not self.measurements_are_ready():
            time.sleep(0.05)

        return [m.get_last_iv_curve() for m in self.measurers]

    def set_settings(self, settings:MeasurementSettings):
        """
        Assign same settings for all measurers.
        """
        pass

    def get_settings(self) -> MeasurementSettings:
        """
        Check wether all measurers have the same settings.
        If the same - return. Else throw RuntimeError.
        """
        return MeasurementSettings()