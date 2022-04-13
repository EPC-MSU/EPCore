"""
IVMeasurer implementation for ASA measurer. High frequency network IVMeasurer.
The old name - Meridian.
"""

import logging
import threading
import time
from ctypes import c_char_p, c_double, c_uint32, CDLL
from typing import Any, Callable, Dict, Optional, Tuple
import numpy as np
from . import IVMeasurerIdentityInformation
from .asa10 import asa
from .base import IVMeasurerBase, cache_curve
from .processing import smooth_curve, interpolate_curve
from .virtual import IVMeasurerVirtual
from ..elements import IVCurve, MeasurementSettings

formatter = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)
logger = logging.getLogger("asa_measurer_logger")
logger.addHandler(stream_handler)
logger.setLevel(logging.INFO)
logger.propagate = False
_FLAGS = 1
_FREQUENCIES = [(1, 197), (5, 816), (10, 1750), (50, 12254), (100, 12254), (400, 49019), (1500, 196078),
                (6000, 787401), (25000, 3225806), (100000, 14285714), (400000, 100000000), (1500000, 100000000),
                (3000000, 100000000), (6000000, 100000000), (12000000, 100000000)]
_RESISTANCES = [[2000, 1000, 200, 100], [300, 100], [2000, 1000, 400, 200], [100], [300, 200], [2000, 400],
                [300], [1000, 200, 100], [400], [670], [300, 100], [2000, 1000, 400, 200, 111]]
_VOLTAGES = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 4.5, 5.0, 6.0, 6.7, 7.5, 10.0]


def _close_on_error(func: Callable):
    """
    Function handles an error when working with IVMeasurerASA.
    :param func: IVMeasurerASA method.
    :return: IVMeasurerASA decorated method.
    """

    def handle(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except (OSError, RuntimeError) as exc:
            raise exc
    return handle


def _get_settings_for_index(index: int) -> Optional[tuple]:
    """
    Function returns measurement settings for given index of settings.
    :param index: index of required measurement settings.
    :return: probe signal frequency, sampling rate, max voltage and
    internal resistance of next measurement settings.
    """

    current_index = 0
    for frequency, sampling_rate in _FREQUENCIES:
        if frequency == 3000000:
            standard_voltages = _VOLTAGES[:-2]
        elif frequency == 6000000:
            standard_voltages = _VOLTAGES[:5]
        elif frequency == 12000000:
            standard_voltages = _VOLTAGES[:3]
        else:
            standard_voltages = _VOLTAGES
        for voltage in standard_voltages:
            for resistance in _RESISTANCES[standard_voltages.index(voltage)]:
                if current_index == index:
                    return frequency, sampling_rate, voltage, resistance
                current_index += 1
    return None


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
    if protocol.lower() != "xmlrpc" or ip_address[:2] != "//":
        raise ValueError("Wrong protocol for ASA measurer")
    return ip_address[2:], port


class IVMeasurerVirtualASA(IVMeasurerVirtual):
    """
    Class for virtual EyePoint ASA device.
    """

    def __init__(self, url: str = "", name: str = "", defer_open: bool = False):
        """
        :param url: URL for device identification in computer system;
        :param name: friendly name (for measurement system);
        :param defer_open: don't open serial port during initialization.
        """

        super().__init__(url, name, defer_open)
        self.__default_settings = MeasurementSettings(internal_resistance=1000., max_voltage=5.,
                                                      probe_signal_frequency=100, sampling_rate=12254)

    def open_device(self):
        self._open = True
        self.set_settings(self.__default_settings)


class IVMeasurerASA(IVMeasurerBase):
    """
    Class for controlling EyePoint ASA devices (EP H10) with API version 1.0.1.
    All instances should be initialized with device URL. Format: xmlrpc://ip_address:port.
    """

    # ASA device additional parameters
    flags: int = _FLAGS
    mode: str = "manual"
    model_nominal: float = 1.0e-7
    model_type: str = "capacitor"
    n_charge_points: int = asa.N_POINTS
    n_points: int = asa.N_POINTS
    _MAX_CALIBRATION_WAIT: int = 1000

    def __init__(self, url: str = "", name: str = "", defer_open: bool = False):
        """
        :param url: URL for device identification in computer system. For
        devices URL will be "xmlrpc://xxx.xxx.xxx.xxx";
        :param name: friendly name (for measurement system);
        :param defer_open: don't open serial port during initialization.
        """

        self._host, self._port = _parse_address(url)
        self._asa_settings: asa.AsaSettings = asa.AsaSettings()
        self._lib: CDLL = asa.get_dll()
        self._logger_for_signals: logging.Logger = logger
        self._name: str = name
        self._server: asa.Server = None
        self._settings: MeasurementSettings = MeasurementSettings(internal_resistance=1000., max_voltage=5.,
                                                                  probe_signal_frequency=100, sampling_rate=12254)
        self._stop_full_calibration: bool = False
        self._timer: threading.Timer = None
        self._NORMAL_NUM_POINTS: int = 100
        self._SMOOTHING_KERNEL_SIZE: int = 5
        if not defer_open:
            self.open_device()
        super().__init__(url, name)

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
        allowable_voltages = {3000000: (1, 1.5, 2, 2.5, 3, 4, 4.5, 5, 6, 6.7),
                              6000000: (1, 1.5, 2, 2.5, 3),
                              12000000: (1, 1.5, 2)}
        v_allowable = allowable_voltages.get(frequency, all_allowable_voltages)
        if voltage not in v_allowable:
            raise ValueError(f"Invalid value of max voltage {voltage} V at the given value of probe signal "
                             f"frequency {frequency} Hz.\nAllowable max voltage values: {v_allowable} V")
        # Check resistances depending on voltages
        resistance = settings.internal_resistance
        allowable_resistances = {1: (100, 200, 1000, 2000),
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
            raise ValueError(f"Invalid value of internal resistance {resistance} Ohm at the given value of max "
                             f"voltage {voltage} V.\nAllowable resistance values: {r_allowable} Ohm")
        return True

    def _convert_to_asa_settings(self, settings: MeasurementSettings):
        """
        Method converts settings to ASA format.
        :param settings: new values of settings.
        """

        self._asa_settings.sampling_rate_hz = c_double(int(settings.sampling_rate))
        self._asa_settings.number_points = c_uint32(asa.N_POINTS)
        self._asa_settings.number_charge_points = c_uint32(self.n_charge_points)
        self._asa_settings.measure_flags = c_uint32(_FLAGS)
        self._asa_settings.probe_signal_frequency_hz = c_double(int(settings.probe_signal_frequency))
        self._asa_settings.voltage_ampl_v = c_double(settings.max_voltage)
        max_current = 1000 * settings.max_voltage / settings.internal_resistance
        if max_current < 1:
            max_current = round(max_current, 1)
        else:
            max_current = int(max_current)
        self._asa_settings.max_current_m_a = c_double(max_current)
        self._asa_settings.debug_model_type = c_uint32(2 * (self.model_type.lower() == "capacitor") +
                                                       (self.model_type.lower() == "resistor"))
        self._asa_settings.trigger_mode = c_uint32(self.mode.lower() == "manual")
        self._asa_settings.debug_model_nominal = c_double(self.model_nominal)

    @staticmethod
    def _get_from_asa_settings(asa_settings: asa.AsaSettings) -> Tuple[MeasurementSettings, Dict]:
        """
        Method gets values of settings from ASA format.
        :param asa_settings: settings in ASA format.
        :return: main and additional measurement settings.
        """

        sampling_rate = int(asa_settings.sampling_rate_hz)
        probe_signal_frequency = int(asa_settings.probe_signal_frequency_hz)
        max_voltage = float(asa_settings.voltage_ampl_v)
        max_current = float(asa_settings.max_current_m_a)
        internal_resistance = int(1000 * max_voltage / max_current)
        if 110 <= internal_resistance <= 112:
            internal_resistance = 111
        n_points = int(asa_settings.number_points)
        n_charge_points = int(asa_settings.number_charge_points)
        flags = int(asa_settings.measure_flags)
        if int(asa_settings.debug_model_type) == asa.COMPONENT_MODEL_TYPE_RESISTOR:
            model_type = "resistor"
        elif int(asa_settings.debug_model_type) == asa.COMPONENT_MODEL_TYPE_CAPACITOR:
            model_type = "capacitor"
        else:
            model_type = "none"
        if int(asa_settings.trigger_mode) == asa.MODE_MANUAL:
            mode = "manual"
        else:
            mode = "auto"
        model_nominal = float(asa_settings.debug_model_nominal)
        precharge_delay = n_charge_points / sampling_rate
        if int(precharge_delay) == 0:
            precharge_delay = None
        settings = MeasurementSettings(sampling_rate=sampling_rate, internal_resistance=internal_resistance,
                                       max_voltage=max_voltage, probe_signal_frequency=probe_signal_frequency,
                                       precharge_delay=precharge_delay)
        additional_settings = {"flags": flags,
                               "mode": mode,
                               "model_nominal": model_nominal,
                               "model_type": model_type,
                               "n_charge_points": n_charge_points,
                               "n_points": n_points}
        return settings, additional_settings

    def _perform_calibration(self, calibration_type: int, calibration_name: str, settings_index: int):
        """
        Method performs calibration of measuring device for measurement settings
        with given index.
        :param calibration_type: type of full calibration;
        :param calibration_name: name of calibration type;
        :param settings_index: index of measurement settings.
        """

        if self._timer:
            self._timer.cancel()
        settings = _get_settings_for_index(settings_index)
        if settings is None:
            self._logger_for_signals.info("Calibration finished")
            return
        frequency, sampling_rate, voltage, resistance = settings
        self._logger_for_signals.info("Frequency = %s Hz, sampling_rate = %s Hz, voltage = %s Ohm, resistance = %s Ohm",
                                      frequency, sampling_rate, voltage, resistance)
        new_settings = MeasurementSettings(internal_resistance=resistance, max_voltage=voltage,
                                           probe_signal_frequency=frequency, sampling_rate=sampling_rate)
        self.set_settings(new_settings)
        self._wait_for_completion()
        self._perform_fast_calibration(calibration_type, calibration_name)
        self._wait_for_completion()
        settings_index += 1
        if not self._stop_full_calibration and settings_index < asa.NUM_COMBINATION:
            self._timer = threading.Timer(0.5, self._perform_calibration, args=(calibration_type, calibration_name,
                                                                                settings_index))
            self._timer.start()

    def _perform_fast_calibration(self, calibration_type: int, calibration_name: str):
        """
        Method performs fast calibration of measuring device.
        :param calibration_type: type of fast calibration;
        :param calibration_name: name of calibration type.
        """

        self._logger_for_signals.info("Start calibration '%s'", calibration_name)
        try:
            assert asa.Calibrate(self._lib, self._server, calibration_type) >= 0
        except AssertionError:
            self._logger_for_signals.error("Failed to start calibration '%s'", calibration_name)
        _ask = 0
        while asa.GetLastOperationResult(self._lib, self._server) == asa.ASA_OK:
            self._logger_for_signals.info("Calibration '%s' is waiting in line", calibration_name)
            _ask += 1
            if _ask > self._MAX_CALIBRATION_WAIT / self._settings.probe_signal_frequency:
                break
            time.sleep(0.05)
        while True:
            time.sleep(0.2)
            if asa.GetLastOperationResult(self._lib, self._server) < 1:
                break
        if asa.GetLastOperationResult(self._lib, self._server) < 0:
            self._logger_for_signals.warning("Calibration '%s' was unsuccessful", calibration_name)
        else:
            self._logger_for_signals.info("Calibration '%s' was successful", calibration_name)

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

    def _wait_for_completion(self):
        """
        Method is waiting for the last operation to complete.
        """

        status = asa.GetLastOperationResult(self._lib, self._server)
        while status != asa.ASA_OK:
            if status in (asa.ASA_CONNECTION_ERROR, asa.SERVER_RESPONSE_ERROR):
                break
            time.sleep(0.2)
            status = asa.GetLastOperationResult(self._lib, self._server)

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
        Method performs calibration of type "Быстрая калибровка. Замкнутые щупы".
        """

        self._perform_fast_calibration(asa.FAST_CLOSE_CALIBRATE, "Fast calibration with closed probes")

    def calibrate_fast_and_open(self):
        """
        Method performs calibration of type "Быстрая калибровка. Разомкнутые щупы".
        """

        self._perform_fast_calibration(asa.FAST_OPEN_CALIBRATE, "Fast calibration with open probes")

    def calibrate_full_and_closed(self):
        """
        Method performs calibration of type "Полная калибровка. Замкнутые щупы".
        """

        self._init_settings = self.get_settings()
        self._stop_full_calibration = False
        self._perform_calibration(asa.FULL_CLOSE_CALIBRATE_AND_SAVE, "Full calibration with closed probes", 0)

    def calibrate_full_and_open(self):
        """
        Method performs calibration of type "Полная калибровка. Разомкнутые щупы".
        """

        self._init_settings = self.get_settings()
        self._stop_full_calibration = False
        self._perform_calibration(asa.FULL_OPEN_CALIBRATE_AND_SAVE, "Full calibration with open probes", 0)

    def close_device(self):
        pass

    def get_current_value_of_parameter(self, attribute_name: str) -> Any:
        """
        Method returns current value of measurer parameter with given name.
        :return: current value of parameter.
        """

        return getattr(self, attribute_name, None)

    @_close_on_error
    def get_identity_information(self) -> IVMeasurerIdentityInformation:
        return IVMeasurerIdentityInformation(manufacturer="Meridian", device_name="ASA device",
                                             device_class="ASA device", hardware_version=tuple(),
                                             firmware_version=(1, 0, 1), name="ASA device", rank=1)

    @cache_curve
    @_close_on_error
    def get_last_iv_curve(self, raw: bool = False) -> IVCurve:
        """
        Method returns measured data from device.
        :param raw: if raw is True postprocessing (averaging) is not applied.
        """

        try:
            curve = asa.IvCurve()
            asa.GetSettings(self._lib, self._server, self._asa_settings)
            result = asa.GetIVCurve(self._lib, self._server, curve, self._asa_settings.number_points)
            if result != asa.ASA_OK:
                raise Exception("Getting IV-curve failed")
            n_points = asa.GetNumberPointsForSinglePeriod(self._lib, self._asa_settings)
        except Exception as exc:
            logging.error("Curve was not received. Something went wrong: %s", exc)
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
            curve = interpolate_curve(curve=curve, final_num_points=self._NORMAL_NUM_POINTS)
        curve = smooth_curve(curve=curve, kernel_size=self._SMOOTHING_KERNEL_SIZE)
        return curve

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
            self.n_points = additional_settings["n_points"]
        return settings

    @_close_on_error
    def measurement_is_ready(self) -> bool:
        if self.is_freezed():
            return False
        return asa.GetLastOperationResult(self._lib, self._server) == asa.ASA_OK

    @_close_on_error
    def open_device(self):
        self._set_server_host()
        try:
            self.set_settings()
            self.get_settings()
        except (asa.AsaFormatError, asa.AsaTypeError, asa.AsaValueError) as exc:
            logging.error("Error occurred while opening ASA measurer: %s", exc)
            raise
        self._wait_for_completion()

    def reconnect(self) -> bool:
        try:
            self.open_device()
            return True
        except (RuntimeError, OSError, asa.AsaConnectionError, asa.AsaServerResponseError):
            return False

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
        self._wait_for_completion()
        self._settings = settings

    def set_value_to_parameter(self, attribute_name: str, value: Any):
        """
        Method sets value to attribute of measurer with given name.
        :param attribute_name: name of attribute;
        :param value: value for attribute.
        """

        if attribute_name in self.__dict__:
            setattr(self, attribute_name, value)

    def stop_full_calibration(self):
        """
        Method to stop full calibration.
        """

        self._stop_full_calibration = True
        if self._timer:
            self._timer.cancel()
        time.sleep(2)
        self.set_settings(self._init_settings)

    @_close_on_error
    def trigger_measurement(self):
        if not self.is_freezed():
            asa.TriggerMeasurement(self._lib, self._server)
