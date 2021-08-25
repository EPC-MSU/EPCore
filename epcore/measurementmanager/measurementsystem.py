import time
from copy import deepcopy
from typing import Dict, List, Optional
import numpy as np
from ..elements import IVCurve, MeasurementSettings
from ..ivmeasurer import IVMeasurerBase


class MeasurementSystem:
    """
    Provide mass operations with a number of IVMeasurers.
    If you have only single IVMeasurer, it is recommended to use
    this class for compatibility.
    """

    measurers: List[IVMeasurerBase]
    measurers_map: Dict[str, IVMeasurerBase]

    def __init__(self, measurers: Optional[List[IVMeasurerBase]] = None):
        self.measurers = measurers or []

        # Two containers for the same thing is not a good feature.
        # Consider removing and try not to use this.
        self.measurers_map = {measurer.name: measurer for measurer in measurers if measurer.name}

    def trigger_measurements(self):
        """
        Trigger measurements on all devices.
        """

        for measurer in self.measurers:
            measurer.trigger_measurement()

    def measurements_are_ready(self) -> bool:
        """
        Return True if all measurers have done their job.
        """

        return all([m.measurement_is_ready() for m in self.measurers if not m.is_freezed()])

    def measure_iv_curves(self) -> List[IVCurve]:
        """
        Make measurements and get new curves from all devices.
        """

        self.trigger_measurements()
        while not self.measurements_are_ready():
            time.sleep(0.05)
        return [measurer.get_last_iv_curve() for measurer in self.measurers]

    def set_settings(self, settings: MeasurementSettings):
        """
        Assign same settings for all measurers.
        """

        for measurer in self.measurers:
            measurer.set_settings(settings)

    def get_settings(self) -> MeasurementSettings:
        """
        Check whether all measurers have the same settings.
        If the same - return. Else throw RuntimeError.
        """

        all_settings = [measurer.get_settings() for measurer in self.measurers]
        if not all_settings:
            raise ValueError("No ivc measurers")
        precision = 0.01
        s0 = all_settings[0]
        for s in all_settings:
            if (not np.isclose(s.internal_resistance, s0.internal_resistance, atol=precision) or
                    s.sampling_rate != s0.sampling_rate or
                    s.probe_signal_frequency != s0.probe_signal_frequency or
                    not np.isclose(s.max_voltage, s0.max_voltage, atol=precision)):
                raise ValueError("Settings are different for measurers")
        return deepcopy(all_settings[0])

    def unfreeze(self):
        """
        Unfreeze all measurers
        """
        for measurer in self.measurers:
            measurer.unfreeze()

    def calibrate(self):
        for measurer in self.measurers:
            measurer.calibrate()

    def reconnect(self) -> bool:
        return all([measurer.reconnect() for measurer in self.measurers])
