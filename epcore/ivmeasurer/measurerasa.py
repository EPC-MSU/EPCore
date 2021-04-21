"""
IVMeasurer implementation for ASA measurer. High frequency network IVMeasurer.
The old name - Meridian.
"""

from ctypes import c_char_p, c_double, c_uint32
from typing import Any, Callable, Dict, Tuple
import numpy as np
from . import IVMeasurerIdentityInformation
from .asa10 import libasa as asa
from .base import IVMeasurerBase, cache_curve
from .processing import smooth_curve, interpolate_curve
from .safe_opener import open_device_safe
from ..elements import IVCurve, MeasurementSettings


def _close_on_error(func: Callable):
    """
    Due to the nature of the uRPC library uRPC device must be immediately
    closed after first error.
    :param func: IVMeasurerIVM10 method.
    :return: IVMeasurerIVM10 decorated method.
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
    if protocol != "xmlrpc":
        raise ValueError("Wrong protocol for ASA measurer")
    return ip_address, port


class IVMeasurerASA(IVMeasurerBase):
    """
    Class for controlling EyePoint ASA devices (EP H10) with API version 1.0.1.
    All instances should be initialized with device URL. Format:
    xmlrpr:xxx.xxx.xxx.xxx:x.
    """

    # ASA device additional parameters
    flags: int
    max_current: float
    mode: str
    model_nominal: float
    model_type: str
    n_charge_points: int
    n_points: int

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
        self._server: asa.Server = None
        self._asa_settings = asa.AsaSettings()
        self._settings: MeasurementSettings = None
        self._FRAME_SIZE = 25
        self._SMOOTHING_KERNEL_SIZE = 5
        self._NORMAL_NUM_POINTS = 100
        if not defer_open:
            self.open_device()
        super().__init__(url, name)

    @_close_on_error
    def open_device(self):
        self._set_server_host()
        self._settings = self.get_settings()

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
        asa.GetSettings(self._server, self._asa_settings)
        settings, additional_settings = self._get_from_asa_settings(self._asa_settings)
        if self._check_settings(settings, additional_settings):
            self.flags = additional_settings["flags"]
            self.max_current = additional_settings["max_current"]
            self.mode = additional_settings["mode"]
            self.model_nominal = additional_settings["model_nominal"]
            self.model_type = additional_settings["model_type"]
            self.n_charge_points = additional_settings["n_charge_points"]
            self.n_points = additional_settings["n_points"]
        return settings

    @_close_on_error
    def set_settings(self, settings: MeasurementSettings = None):
        if settings is None:
            settings = self._settings
        try:
            self._convert_to_asa_settings(settings)
            status = asa.SetSettings(self._server, self._asa_settings)
            assert status >= 0
            self._settings = settings
        except AssertionError:
            self.logger.error("SetSettings failed: %s", str(status))

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
            asa.TriggerMeasurement(self._server)

    @_close_on_error
    def measurement_is_ready(self) -> bool:
        if self.is_freezed():
            return False
        return True

    @_close_on_error
    def calibrate(self, *args):
        """
        Calibrate ASA device.
        :param args: arguments.
        """

        # TODO: calibration settings?
        pass

    @cache_curve
    @_close_on_error
    def get_last_iv_curve(self, raw: bool = False) -> IVCurve:
        """
        Return measured data from device.
        :param raw: if raw is True postprocessing (averaging) is not applied.
        """

        curve = asa.IvCurve()
        asa.GetIVCurve(self._server, curve, self._asa_settings.number_points)
        try:
            asa.GetSettings(self._server, self._asa_settings)
            assert asa.GetIVCurve(self._server, curve, self._asa_settings.number_points) == 0
        except AssertionError:
            self.logger.error("Curve was not received. Something went wrong!")
            return None, None
        except OSError:
            self.logger.error("Curve was not received!")
            return None, None
        # Device return currents in mA
        currents = curve.currents
        voltages = curve.voltages
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
    def _check_settings(settings: MeasurementSettings, additional_settings: Tuple) -> bool:
        """
        Method checks settings of ASA device on correctness.
        :param settings: main settings;
        :param additional_settings: additional settings for ASA device.
        :return: True if settings is correct.
        """

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
        self._asa_settings.probe_signal_frequency_hz = c_double(int(settings.probe_signal_frequency))
        self._asa_settings.voltage_ampl_v = c_double(settings.max_voltage)
        self._asa_settings.max_current_m_a = c_double(self.max_current)
        self._asa_settings.debug_model_type = \
            c_uint32(2 * (self.model_type.lower() == "capacitor") + (self.model_type.lower() == "resistor"))
        self._asa_settings.trigger_mode = c_uint32(self.mode == "Manual")
        self._asa_settings.debug_model_nominal = c_double(self.model_nominal)

    @staticmethod
    def _get_from_asa_settings(asa_settings) -> Tuple[MeasurementSettings, Dict]:
        """
        Method get values of settings from ASA format.
        :return: main and additional measurement settings.
        """

        sampling_rate = int(asa_settings.sampling_rate_hz)
        probe_signal_frequency = int(asa_settings.probe_signal_frequency_hz)
        max_current = float(asa_settings.voltage_ampl_v)
        max_voltage = float(asa_settings.max_current_m_a)
        internal_resistance = max_voltage / max_current
        n_points = int(asa_settings.number_points)
        n_charge_points = int(asa_settings.number_charge_points)
        flags = int(asa_settings.measure_flags)
        if int(asa_settings.debug_model_type) == 1:
            model_type = "resistor"
        else:
            model_type = "capacitor"
        if int(asa_settings.trigger_mode) == 1:
            mode = "Manual"
        else:
            mode = "Auto"
        model_nominal = float(asa_settings.debug_model_nominal)
        precharge_delay = n_charge_points / sampling_rate
        if int(precharge_delay) == 0:
            precharge_delay = None
        settings = MeasurementSettings(
            sampling_rate=sampling_rate,
            internal_resistance=internal_resistance,
            max_voltage=max_voltage,
            probe_signal_frequency=probe_signal_frequency,
            precharge_delay=precharge_delay)
        additional_settings = {"flags": flags,
                               "max_current": max_current,
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
            self.logger.info("Server host is empty!")
            return
        c_host = c_char_p(self._host.encode("utf-8"))
        c_port = c_char_p(self._port.encode("utf-8"))
        self._server = asa.Server(c_host, c_port)
