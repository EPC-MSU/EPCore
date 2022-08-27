"""
File with class for virtual current-voltage measurer.
"""

import copy
import logging
import time
from typing import Any, Callable, List, Tuple
import numpy as np
from epcore.ivmeasurer.base import cache_curve, IVMeasurerBase, IVMeasurerIdentityInformation
from epcore.ivmeasurer.processing import interpolate_curve, smooth_curve
from epcore.elements import IVCurve, MeasurementSettings


def _check_open(func: Callable):
    def handler(self: "IVMeasurerVirtual", *args, **kwargs):
        if not self._open:
            raise RuntimeError("Device is not opened")
        return func(self, *args, **kwargs)
    return handler


class IVMeasurerVirtual(IVMeasurerBase):
    """
    Virtual IVMeasurer.
    """

    def __init__(self, url: str = "", name: str = "", defer_open: bool = False):
        """
        :param url: url for device identification in computer system. For
        serial devices url will be "com:\\\\.\\COMx" (for Windows) or "com:///dev/tty/ttyACMx" (for Linux);
        :param name: friendly name (for measurement system);
        :param defer_open: don't open serial port during initialization.
        """

        self.url = url
        self.__default_settings: MeasurementSettings = MeasurementSettings(sampling_rate=10000,
                                                                           internal_resistance=4750,
                                                                           max_voltage=5, probe_signal_frequency=100)
        self.__last_curve: IVCurve = IVCurve()
        self.__measurement_is_ready: bool = False
        self.__ready_time = 0
        self.__settings: MeasurementSettings = None
        self._open: bool = False
        self.model: str = "resistor"
        self.noise_factor: float = 0.05
        self.nominal: float = 100
        self.phase: float = 0
        self._NORMAL_NUM_POINTS = 100
        self._SMOOTHING_KERNEL_SIZE = 5
        if not defer_open:
            self.open_device()
        logging.debug("IVMeasurerVirtual created")
        super().__init__(url, name)

    def open_device(self):
        self._open = True
        self.set_settings(self.__default_settings)

    def reconnect(self) -> bool:
        self.open_device()
        return True

    def close_device(self):
        self._open = False

    @_check_open
    def set_settings(self, settings: MeasurementSettings = None):
        if settings:
            self.__settings = settings

    @_check_open
    def get_settings(self) -> MeasurementSettings:
        return self.__settings

    @_check_open
    def get_identity_information(self) -> IVMeasurerIdentityInformation:
        return IVMeasurerIdentityInformation(manufacturer="EPC MSU", device_class="EyePoint virtual device",
                                             device_name="Virtual IV Measurer", hardware_version=(0, 0, 0),
                                             firmware_version=(0, 0, 0), name="Virtual", rank=0)

    @_check_open
    def trigger_measurement(self):
        """
        Trigger measurement manually. You don’t need this if the hardware is
        in continuous mode.
        """

        if self.is_freezed():
            return
        self.__measurement_is_ready = False
        if self.model == "resistor":
            self.__last_curve = self.__calculate_r_iv()
        elif self.model == "capacitor":
            self.__last_curve = self.__calculate_c_iv()
        else:
            raise NotImplementedError
        self.__measurement_is_ready = False
        self.__ready_time = time.time() + 2. / self.__settings.probe_signal_frequency

    @_check_open
    def measurement_is_ready(self) -> bool:
        """
        Return True if new measurement is ready.
        """

        if self.is_freezed():
            return False
        if time.time() > self.__ready_time:
            self.__measurement_is_ready = True
        return self.__measurement_is_ready

    @_check_open
    def calibrate(self, *args):
        """
        We don't need to calibrate virtual IVC.
        :param args: arguments.
        """

        pass

    @_check_open
    @cache_curve
    def get_last_iv_curve(self) -> IVCurve:
        """
        Return result of the last measurement.
        """

        if self.__measurement_is_ready is not True:
            raise RuntimeError("Measurement is not ready")
        curve = copy.deepcopy(self.__last_curve)
        curve = interpolate_curve(curve=curve, final_num_points=self._NORMAL_NUM_POINTS)
        curve = smooth_curve(curve=curve, kernel_size=self._SMOOTHING_KERNEL_SIZE)
        return curve

    @_check_open
    def get_current_value_of_parameter(self, attribute_name: str) -> Any:
        """
        Method returns current value of measurer parameter with given name.
        :return: current value of parameter.
        """

        return getattr(self, attribute_name, None)

    @_check_open
    def set_value_to_parameter(self, attribute_name: str, value: Any):
        """
        Method sets value to attribute of measurer with given name.
        :param attribute_name: name of attribute;
        :param value: value for attribute.
        """

        if attribute_name in self.__dict__:
            setattr(self, attribute_name, value)

    def __add_noise(self, voltages: List[float], currents: List[float]) -> Tuple[List[float], List[float]]:
        """
        Method adds noise to values of voltages and currents.
        :param voltages: list of voltage values;
        :param currents: list of current values.
        :return: lists of voltage values and current values with noise.
        """

        v_noise_ampl = self.__settings.max_voltage * self.noise_factor
        voltages = np.array(voltages) + v_noise_ampl * (2 * np.random.random(len(voltages)) - 1)
        i_noise_ampl = self.__settings.max_voltage / (self.__settings.internal_resistance + 100) * self.noise_factor
        currents = np.array(currents) + i_noise_ampl * (2 * np.random.random(len(currents)) - 1)
        return voltages, currents

    def __calculate_r_iv(self) -> IVCurve:
        """
        Method calculates current and voltage with generated settings with resistor.
        """

        f = self.__settings.probe_signal_frequency
        r = self.__settings.internal_resistance
        n_points = self.__settings.sampling_rate // f
        t = np.linspace(0, 1 / f, n_points)
        v_in = self.__settings.max_voltage * np.sin(self.phase + 2 * np.pi * f * t)
        #                  R
        # V_out = V_in ---------; R - model of connected resistor under test
        #               R + R_cs
        v_out = v_in * self.nominal / (self.nominal + r)
        # I_out = V_out / R
        i_out = v_out / self.nominal
        v_out, i_out = self.__add_noise(v_out, i_out)
        return IVCurve(currents=i_out.tolist(), voltages=v_out.tolist())

    def __calculate_c_iv(self) -> IVCurve:
        """
        Method calculates current and voltage with generated settings with capacitor.
        """

        f = self.__settings.probe_signal_frequency
        c = self.nominal
        r = self.__settings.internal_resistance
        # Total circuit resistance
        z = np.sqrt(np.power(2 * np.pi * f * c, -2) + np.power(r, 2))
        # Max charge on the capacitor
        q0 = self.__settings.max_voltage / (2 * np.pi * f * z)
        phi = np.arctan(2 * np.pi * f * c * r)
        n_points = self.__settings.sampling_rate // f
        t = np.linspace(0, 1 / f, n_points)
        v_out = q0 / c * np.cos(self.phase + 2 * np.pi * f * t - phi)
        i_out = 2 * np.pi * f * q0 * np.sin(self.phase + 2 * np.pi * f * t - phi)
        v_out, i_out = self.__add_noise(v_out, i_out)
        return IVCurve(currents=i_out.tolist(), voltages=v_out.tolist())
