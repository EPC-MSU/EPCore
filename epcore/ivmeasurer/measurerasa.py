"""
IVMeasurer implementation for ASA measurer. High frequency network IVMeasurer.
The old name - Meridian.
"""

import logging
import time
from ctypes import c_char_p, c_double, c_uint32
from typing import Any, Callable, Dict, Tuple
import numpy as np
from . import IVMeasurerIdentityInformation
from .asa10 import asa
from .base import IVMeasurerBase, cache_curve
from .processing import smooth_curve, interpolate_curve
from .virtual import IVMeasurerVirtual
from ..elements import IVCurve, MeasurementSettings


def _close_on_error(func: Callable):
    """
    Function handles an error when working with IVMeasurerASA.
    :param func: IVMeasurerASA method.
    :return: IVMeasurerASA decorated method.
    """

    def handle(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except (RuntimeError, OSError) as err:
            raise err
    return handle


def _parse_address(full_address: str) -> Tuple[str, str]:
    """
    Function parses full device address into its component parts.
    :param full_address: full device address.
    :return: IP address and port of device.
    """

    address_parts = full_address.split(":")
    port = None
    if len(address_parts) == 3:
        protocol, ip_address, port = address_parts
    else:
        protocol, ip_address = address_parts
    if protocol.lower() != "xmlrpc":
        raise ValueError("Wrong protocol for ASA measurer")
    return ip_address, port


class IVMeasurerVirtualASA(IVMeasurerVirtual):
    """
    Class for virtual EyePoint ASA device.
    """

    def __init__(self, url: str = "", name: str = "",
                 defer_open: bool = False):
        """
        :param url: url for device identification in computer system. For
        serial devices url will be "com:\\\\.\\COMx" (for Windows) or
        "com:///dev/tty/ttyACMx" (for Linux);
        :param name: friendly name (for measurement system);
        :param defer_open: don't open serial port during initialization.
        """

        super().__init__(url, name, defer_open)
        self.__default_settings = MeasurementSettings(
            internal_resistance=1000.,
            max_voltage=5.,
            probe_signal_frequency=100,
            sampling_rate=12254)

    def open_device(self):
        self._open = True
        self.set_settings(self.__default_settings)


class IVMeasurerASA(IVMeasurerBase):
    """
    Class for controlling EyePoint ASA devices (EP H10) with API version 1.0.1.
    All instances should be initialized with device URL. Format:
    xmlrpc:ip_address:port.
    """

    _calibration_types = {"Быстрая калибровка. Замкнутые щупы": 0,
                          "Быстрая калибровка. Разомкнутые щупы": 1,
                          "Полная калибровка. Замкнутые щупы": 2,
                          "Полная калибровка. Разомкнутые щупы": 3}

    # ASA device additional parameters
    flags: int = 3
    mode: str = "manual"
    model_nominal: float = 1.0e-7
    model_type: str = "capacitor"
    n_charge_points: int = 512
    n_points: int = 512

    def __init__(self, url: str = "", name: str = "",
                 defer_open: bool = False):
        """
        :param url: url for device identification in computer system. For
        devices url will be "xmlrpc:xxx.xxx.xxx.x";
        :param name: friendly name (for measurement system);
        :param defer_open: don't open serial port during initialization.
        """

        self._host, self._port = _parse_address(url)
        self._name = name
        self._lib = asa.get_dll()
        self._server: asa.Server = None
        self._asa_settings = asa.AsaSettings()
        self._settings = MeasurementSettings(
            internal_resistance=1000.,
            max_voltage=5.,
            probe_signal_frequency=100,
            sampling_rate=12254)
        self._measurement_is_ready: bool = False
        self._SMOOTHING_KERNEL_SIZE = 5
        self._NORMAL_NUM_POINTS = 100
        if not defer_open:
            self.open_device()
        super().__init__(url, name)

    @_close_on_error
    def open_device(self):
        self._set_server_host()
        attempt_number = 0
        while attempt_number < 3:
            try:
                self.set_settings()
                self.get_settings()
            except Exception:
                attempt_number += 1
                continue
            break
        while asa.GetLastOperationResult(self._lib, self._server) != 0:
            time.sleep(0.2)

    def close_device(self):
        pass

    def reconnect(self) -> bool:
        try:
            self.open_device()
            return True
        except (RuntimeError, OSError):
            return False

    @_close_on_error
    def get_settings(self) -> MeasurementSettings:
        asa.GetSettings(self._lib, self._server, self._asa_settings)
        settings, additional_settings = self._get_from_asa_settings(self._asa_settings)
        if self._check_settings(settings):
            self.flags = additional_settings["flags"]
            self.mode = additional_settings["mode"]
            self.model_nominal = additional_settings["model_nominal"]
            self.model_type = additional_settings["model_type"]
            self.n_charge_points = additional_settings["n_charge_points"]
            # self.n_points = additional_settings["n_points"]
        return settings

    @_close_on_error
    def set_settings(self, settings: MeasurementSettings = None):
        if settings is None:
            settings = self._settings
        self._check_settings(settings)
        self._convert_to_asa_settings(settings)
        status = asa.SetSettings(self._lib, self._server, self._asa_settings)
        if status != 0:
            logging.error("SetSettings failed: %s", str(status))
            raise Exception("SetSettings failed")
        self._settings = settings

    @_close_on_error
    def get_identity_information(self) -> IVMeasurerIdentityInformation:
        return IVMeasurerIdentityInformation(
            manufacturer="Meridian",
            device_name="ASA device",
            device_class="ASA device",
            hardware_version=tuple(),
            firmware_version=(1, 0, 1),
            name="ASA device",
            rank=1)

    @_close_on_error
    def trigger_measurement(self):
        if not self.is_freezed():
            self._measurement_is_ready = False
            asa.TriggerMeasurement(self._lib, self._server)
            while asa.GetLastOperationResult(self._lib, self._server) != 0:
                time.sleep(0.2)
            self._measurement_is_ready = True

    @_close_on_error
    def measurement_is_ready(self) -> bool:
        if self.is_freezed():
            return False
        return self._measurement_is_ready

    @_close_on_error
    def calibrate(self, value: int):
        """
        Calibrate ASA device.
        :param value: parameter that determines type of calibration.
        """

        try:
            result = asa.Calibrate(self._lib, self._server, value)
            assert result >= 0
        except AssertionError:
            logging.error("Calibration has not been performed")

    def calibrate_fast_and_closed(self):
        """
        Method performes calibration of type "Быстрая калибровка. Замкнутые
        щупы".
        """

        self.calibrate(self._calibration_types["Быстрая калибровка. Замкнутые щупы"])

    def calibrate_fast_and_open(self):
        """
        Method performes calibration of type "Быстрая калибровка. Разомкнутые
        щупы".
        """

        self.calibrate(self._calibration_types["Быстрая калибровка. Разомкнутые щупы"])

    def calibrate_full_and_closed(self):
        """
        Method performes calibration of type "Полная калибровка. Замкнутые
        щупы".
        """

        self.calibrate(self._calibration_types["Полная калибровка. Замкнутые щупы"])

    def calibrate_full_and_open(self):
        """
        Method performes calibration of type "Полная калибровка. Разомкнутые
        щупы".
        """

        self.calibrate(self._calibration_types["Полная калибровка. Разомкнутые щупы"])

    @cache_curve
    @_close_on_error
    def get_last_iv_curve(self, raw: bool = False) -> IVCurve:
        """
        Return measured data from device.
        :param raw: if raw is True postprocessing (averaging) is not applied.
        """

        curve = asa.IvCurve()
        asa.GetIVCurve(self._lib, self._server, curve, self._asa_settings.number_points)
        try:
            asa.GetSettings(self._lib, self._server, self._asa_settings)
            assert asa.GetIVCurve(self._lib, self._server, curve,
                                  self._asa_settings.number_points) == 0
            n_points = asa.GetNumberPointsForSinglePeriod(self._lib, self._asa_settings)
        except AssertionError:
            logging.error("Curve was not received. Something went wrong")
            if self._cashed_curve:
                return self._cashed_curve
            return IVCurve()
        except OSError:
            logging.error("Curve was not received")
            if self._cashed_curve:
                return self._cashed_curve
            return IVCurve()
        # Device return currents in mA
        currents = list(np.array(curve.currents[:n_points]) / 1000)
        voltages = curve.voltages[:n_points]
        curve = IVCurve(currents=currents, voltages=voltages)
        if raw is True:
            return curve
        # Postprocessing
        if self._asa_settings.probe_signal_frequency_hz > 20000:
            curve = interpolate_curve(curve=curve,
                                      final_num_points=self._NORMAL_NUM_POINTS)
        curve = smooth_curve(curve=curve,
                             kernel_size=self._SMOOTHING_KERNEL_SIZE)
        return curve

    def get_current_value_of_parameter(self, attribute_name: str) -> Any:
        """
        Method returns current value of measurer parameter with given name.
        :return: current value of parameter.
        """

        return getattr(self, attribute_name, None)

    def set_value_to_parameter(self, attribute_name: str, value: Any):
        """
        Method sets value to attribute of measurer with given name.
        :param attribute_name: name of attribute;
        :param value: value for attribute.
        """

        if attribute_name in self.__dict__:
            setattr(self, attribute_name, value)

    @staticmethod
    def _check_settings(settings: MeasurementSettings) -> bool:
        """
        Method checks settings of ASA device on correctness.
        :param settings: main settings.
        :return: True if settings is correct.
        """

        # Check voltages depending on frequency
        frequency = settings.probe_signal_frequency
        voltage = settings.max_voltage
        all_allowable_voltages = (1, 1.5, 2, 2.5, 3, 4, 4.5, 5, 6, 6.7, 7.5, 10)
        allowable_voltages = {
            3000000: (1, 1.5, 2, 2.5, 3, 4, 4.5, 5, 6, 6.7),
            6000000: (1, 1.5, 2, 2.5, 3),
            12000000: (1, 1.5, 2)}
        v_allowable = allowable_voltages.get(frequency, all_allowable_voltages)
        if voltage not in v_allowable:
            msg = (f"Invalid value of max voltage {voltage} V at the given value of "
                   f"probe signal frequency {frequency} Hz.\n"
                   f"Allowable max voltage values: {v_allowable} V")
            raise ValueError(msg)
        # Check resistances depending on voltages
        resistance = settings.internal_resistance
        allowable_resistances = {
            1: (100, 200, 1000, 2000),
            1.5: (100, 300),
            2: (200, 400, 1000, 2000),
            2.5: (100,),
            3: (200, 300),
            4: (400, 2000),
            4.5: (300,),
            5: (100, 200, 1000),
            6: (400,),
            6.7: (670,),
            7.5: (100, 300),
            10: (111, 200, 400, 1000, 2000)}
        r_allowable = allowable_resistances.get(voltage, tuple())
        if resistance not in r_allowable:
            msg = (f"Invalid value of internal resistance {resistance} Ohm at "
                   f"the given value of max voltage {voltage} V.\n"
                   f"Allowable resistance values: {r_allowable} Ohm")
            raise ValueError(msg)
        return True

    def _convert_to_asa_settings(self, settings: MeasurementSettings):
        """
        Method converts settings to ASA format.
        :param settings: new values of settings.
        """

        self._asa_settings.sampling_rate_hz = c_double(int(settings.sampling_rate))
        self._asa_settings.number_points = c_uint32(self.n_points)
        self._asa_settings.number_charge_points = c_uint32(self.n_charge_points)
        self._asa_settings.measure_flags = c_uint32(self.flags)
        self._asa_settings.probe_signal_frequency_hz = \
            c_double(int(settings.probe_signal_frequency))
        self._asa_settings.voltage_ampl_v = c_double(settings.max_voltage)
        max_current = round(1000 * settings.max_voltage / settings.internal_resistance, 1)
        self._asa_settings.max_current_m_a = c_double(max_current)
        self._asa_settings.debug_model_type = \
            c_uint32(2 * (self.model_type.lower() == "capacitor") +
                     (self.model_type.lower() == "resistor"))
        self._asa_settings.trigger_mode = c_uint32(self.mode.lower() == "manual")
        self._asa_settings.debug_model_nominal = c_double(self.model_nominal)

    @staticmethod
    def _get_from_asa_settings(asa_settings: asa.AsaSettings) ->\
            Tuple[MeasurementSettings, Dict]:
        """
        Method gets values of settings from ASA format.
        :return: main and additional measurement settings.
        """

        sampling_rate = int(asa_settings.sampling_rate_hz)
        probe_signal_frequency = int(asa_settings.probe_signal_frequency_hz)
        max_voltage = float(asa_settings.voltage_ampl_v)
        max_current = float(asa_settings.max_current_m_a)
        internal_resistance = int(1000 * max_voltage / max_current)
        n_points = int(asa_settings.number_points)
        n_charge_points = int(asa_settings.number_charge_points)
        flags = int(asa_settings.measure_flags)
        if int(asa_settings.debug_model_type) == 1:
            model_type = "resistor"
        else:
            model_type = "capacitor"
        if int(asa_settings.trigger_mode) == 1:
            mode = "manual"
        else:
            mode = "auto"
        model_nominal = float(asa_settings.debug_model_nominal)
        precharge_delay = n_charge_points / sampling_rate
        if int(precharge_delay) == 0:
            precharge_delay = None
        settings = MeasurementSettings(sampling_rate=sampling_rate,
                                       internal_resistance=internal_resistance,
                                       max_voltage=max_voltage,
                                       probe_signal_frequency=probe_signal_frequency,
                                       precharge_delay=precharge_delay)
        additional_settings = {"flags": flags,
                               "mode": mode,
                               "model_nominal": model_nominal,
                               "model_type": model_type,
                               "n_charge_points": n_charge_points,
                               "n_points": n_points}
        return settings, additional_settings

    def _set_server_host(self):
        """
        Method sets device host.
        """

        if self._port is None:
            self._port = "8888"
        try:
            assert len(self._host) > 0
        except AssertionError:
            logging.error("Server host is empty")
            return
        c_host = c_char_p(self._host.encode("utf-8"))
        c_port = c_char_p(self._port.encode("utf-8"))
        self._server = asa.Server(c_host, c_port)