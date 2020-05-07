from typing import List
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

    def get_iv_curves(self) -> List[IVCurve]:
        """
        Get curves from all devices.
        """
        return []

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