from typing import List, Optional, Dict
import time
import numpy as np
from copy import deepcopy
from ..elements import MeasurementSettings, IVCurve
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
        self.measurers_map = {measurer.name: measurer for measurer in measurers if measurer.name}

    def __smooth_curve(self, curve: IVCurve, kernel_size: int) -> IVCurve:
        """
        Remove noise by averaging
        :param curve: list or tuple of two arrays with voltages and currents
        :param kernel_size: size of averaging kernel. Should be odd.
        :return: averaged curve in format same to the curve
        """

        if kernel_size % 2 == 0:
            raise ValueError("kernel_size should be odd")

        kernel = np.ones(kernel_size) / kernel_size

        smoothed_curve = []
        lines = [curve.voltages, curve.currents]
        for line in lines:
            line = np.array(line)
            line = np.concatenate((line[-(kernel_size - 1) // 2:], line, line[:(kernel_size - 1) // 2]))
            line = np.convolve(line, kernel, mode="valid")
            smoothed_curve.append(line)

        curve.voltages = smoothed_curve[0]
        curve.currents = smoothed_curve[1]

        return curve

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
        return all([m.measurement_is_ready() for m in self.measurers if not m.is_freezed()])

    def measure_iv_curves(self) -> List[IVCurve]:
        """
        Make measurements and
        get new curves from all devices.
        """
        self.trigger_measurements()

        while not self.measurements_are_ready():
            time.sleep(0.05)

        return [m.get_last_iv_curve() for m in self.measurers]

    def get_processed_curves(self, smooth_points: int) -> List[IVCurve]:
        curves = self.measure_iv_curves()

        curves = [self.__smooth_curve(curve, smooth_points) for curve in curves]

        return curves

    def set_settings(self, settings: MeasurementSettings):
        """
        Assign same settings for all measurers.
        """
        for measurer in self.measurers:
            measurer.set_settings(settings)

    def get_settings(self) -> MeasurementSettings:
        """
        Check wether all measurers have the same settings.
        If the same - return. Else throw RuntimeError.
        """
        all_settings = [s.get_settings() for s in self.measurers]

        if not all_settings:
            raise ValueError("No ivc measurers")

        if not all(all_settings[0] == s for s in all_settings):
            raise ValueError("Settings are different for measurers")

        return deepcopy(all_settings[0])

    def unfreeze(self):
        """
        Unfreeze all measurers
        :return:
        """
        for m in self.measurers:
            m.unfreeze()

    def calibrate(self):
        for m in self.measurers:
            m.calibrate()

    def reconnect(self) -> bool:
        return all([m.reconnect() for m in self.measurers])
