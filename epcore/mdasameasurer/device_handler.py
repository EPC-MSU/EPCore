"""
File with class for Meridian device handler.
"""

from __future__ import print_function
import logging
import os
import time
from ctypes import c_char_p, c_double, c_uint32
from typing import Tuple
import numpy as np
from . import libasa as asa
from .elements import CalibrationTypes, MeasurementSettings


__all__ = ["MdasaDeviceHandler", "compare_ivc"]


REQUIRED_LIBASA_VERSION_MAJOR = 0
REQUIRED_LIBASA_VERSION_MINOR = 3
REQUIRED_LIBASA_VERSION_BUGFIX_MIN = 1


def check_libasa_version():
    """
    Function checks libasa version. If found version is not correct function
    raises exception.
    """

    lib_version = asa.GetLibraryVersion()
    if (lib_version[0] == REQUIRED_LIBASA_VERSION_MAJOR and
        lib_version[1] == REQUIRED_LIBASA_VERSION_MINOR and
            lib_version[2] >= REQUIRED_LIBASA_VERSION_BUGFIX_MIN):
        return
    major = REQUIRED_LIBASA_VERSION_MAJOR
    minor = REQUIRED_LIBASA_VERSION_MINOR
    bugfix = REQUIRED_LIBASA_VERSION_BUGFIX_MIN
    raise RuntimeError(
        f"libasa version should be {major}.{minor}.{bugfix} or greater. "
        f"libasa version  {lib_version[0]}.{lib_version[1]}.{lib_version[2]} found")


def compare_ivc(ivc_1, ivc_2=None) -> float:
    """
    Function compares two current-voltage curves.
    :param ivc_1: first current-voltage curve;
    :param ivc_2: second current-voltage curve.
    :return: difference of curves.
    """

    iv_curve_1 = asa.IvCurve()
    iv_curve_2 = asa.IvCurve()
    result_score = 0.0

    # There are several methods for MinVar setup (see #42980). We will use
    # the first and now it is not adjusted. Some additional adjustment may
    # be required
    # TODO: Make normal class for IVC
    min_v = 0.05 * ivc_1[0][4]  # max_voltage
    min_c = 0.05 * ivc_1[0][5]  # max_current
    if ivc_1 != (None, None):
        n_points_1 = len(ivc_1[1][1])
        iv_curve_1.length = n_points_1
        for i in range(n_points_1):  # a[0][2] = number_points
            iv_curve_1.currents[i] = ivc_1[1][1][i]
            iv_curve_1.voltages[i] = ivc_1[1][0][i]
        if ivc_2 != (None, None):
            n_points_2 = len(ivc_2[1][1])
            iv_curve_2.length = n_points_2
            for i in range(n_points_2):
                iv_curve_2.currents[i] = ivc_2[1][1][i]
                iv_curve_2.voltages[i] = ivc_2[1][0][i]
            asa.SetMinVC(min_v, min_c)
            result_score = asa.CompareIvc(iv_curve_1, iv_curve_2)
        else:
            asa.SetMinVC(max(min_v, 0.6), max(min_c, 0.0002))
            result_score = asa.CompareIvc(iv_curve_1, iv_curve_1)
    return result_score


class MdasaDeviceHandler:
    """
    Class to handle Meridian device. Allows to get/set device settings and
    get IV-curves.
    """

    _max_calibration_wait = 1000

    def __init__(self):
        self.settings = MeasurementSettings(
            sampling_rate=1000.,
            probe_signal_frequency=10.,
            max_voltage=2.,
            max_current=1.,
            n_points=512,
            n_charge_points=400,
            flags=3,
            model_type="",
            model_nominal=0,
            mode="Auto")
        self._host: str = ""
        self._port: str = ""
        self.logger = logging
        self.server = None
        self.asa_settings = asa.AsaSettings()
        self.result = None
        self.save_result = None
        self.save_settings = None
        self.temp_probes = ((0, 0), (0, 0))
        self.connection_status: bool = False
        self.calibration_status = ("", "")
        self.calibrate_state: bool = False
        self.coefficients = asa.AsaCoefficients()

    def _recalculate_period_curve(self, curve):
        if self.asa_settings.probe_signal_frequency_hz < 50:
            n = int(9 / 8 * asa.GetNumberPointsForSinglePeriod(self.asa_settings))
            res = np.zeros((2, n), dtype=np.float32)
            res[1][:n] = curve.currents[n: 2 * n]
            res[0][:n] = curve.voltages[n: 2 * n]
        else:
            n = asa.GetNumberPointsForSinglePeriod(self.asa_settings)
            res = np.zeros((2, n + 1), dtype=np.float32)
            res[1][:n] = curve.currents[:n]
            res[0][:n] = curve.voltages[:n]
            res[1][n] = curve.currents[0]
            res[0][n] = curve.voltages[0]
        return res

    def calibrate(self, value: str):
        self.calibrate_state = True
        try:
            result = asa.Calibrate(self.server, CalibrationTypes[value])
            assert result >= 0
        except AssertionError:
            self.logger.error("{} не запустилась!".format(value.split(".")[0]))
        _ask = 0
        while self.get_status_operation() == 0:
            self.logger.info("Calibration waiting in line...")
            _ask += 1
            if ("Быстрая калибровка" in value.split(".")[0] and
                    _ask > self._max_calibration_wait / self.settings.probe_signal_frequency):
                break
            time.sleep(0.05)
        while True:
            time.sleep(0.2)
            if self.get_status_operation() < 1:
                break
        if self.get_status_operation() < 0:
            self.logger.info("Calibration was unsuccessful!")
            return
        if "Разомкнутые щупы" in value:
            self.calibration_status = ("Калибровка окончена!", value.split(".")[0])
            self.logger.info("Calibration was successful!")
        elif "Замкнутые щупы" in value:
            self.calibration_status = ("Разомкните щупы и нажмите Далее для продолжения!",
                                       value.split(".")[0])
        self.get_and_save_coefficient()
        self.calibrate_state = False

    @staticmethod
    def check_lib_version():
        """
        Method gets libasa version.
        """

        version = asa.GetLibraryVersion()
        print(f"Libasa version: {version[0]}.{version[1]}.{version[2]}")

    def freeze_ivc(self):
        self.save_settings = self.settings
        self.save_result = self.result

    def get_and_save_coefficient(self):
        c_file = c_char_p("coefficients.txt".encode("utf-8"))
        try:
            status = asa.GetCoefficients(self.server, self.coefficients)
            assert status >= 0
            asa.SaveCoefficients(c_file, self.coefficients)
            self.connection_status = True
        except AssertionError:
            self.connection_status = (status != -1)
            self.logger.error("GetCoefficients failed: %s", str(status))

    def get_settings(self) -> MeasurementSettings:
        """
        Method returns measurement settings in Meridian device.
        :return: measurement settings.
        """

        asa.GetSettings(self.server, self.asa_settings)
        self.settings.sampling_rate = int(self.asa_settings.sampling_rate_hz)
        self.settings.probe_signal_frequency = int(self.asa_settings.probe_signal_frequency_hz)
        self.settings.max_current = float(self.asa_settings.voltage_ampl_v)
        self.settings.max_voltage = float(self.asa_settings.max_current_m_a)
        self.settings.n_points = int(self.asa_settings.number_points)
        self.settings.n_charge_points = int(self.asa_settings.number_charge_points)
        self.settings.flags = int(self.asa_settings.measure_flags)
        if int(self.asa_settings.debug_model_type) == 1:
            self.settings.model_type = "Resistor"
        else:
            self.settings.model_type = "Capacitor"
        if int(self.asa_settings.trigger_mode) == 1:
            self.settings.mode = "Manual"
        else:
            self.settings.mode = "Auto"
        self.settings.model_nominal = float(self.asa_settings.debug_model_nominal)
        return self.settings

    def get_status_button_probes(self):
        if not self.server or self.calibrate_state:
            return
        probe_buttons = asa.Buttons()
        try:
            assert asa.GetStatusButtons(self.server, probe_buttons) == 0
        except AssertionError:
            logging.error("GetStatusButtons didn't success!")
            return
        if probe_buttons.gray_button and probe_buttons.blue_button:
            self.calibration_status =\
                ("Замкните щупы, уложите провода щупов параллельно друг другу "
                 "и нажмите Далее, чтобы продолжить!",
                 "Быстрая калибровка. Замкнутые щупы".split(".")[0])
        elif (not probe_buttons.blue_button and probe_buttons.gray_button and
              self.settings.mode == "Manual"):
            self.make_measurement()
        elif not probe_buttons.gray_button and probe_buttons.blue_button:
            self.freeze_ivc()
            logging.info("Curve was freeze! State of blue button: %s",
                         str(probe_buttons.blue_button))

    def get_status_operation(self) -> int:
        try:
            _status = asa.GetLastOperationResult(self.server)
            assert _status >= 0
            self.connection_status = True
        except AssertionError:
            self.connection_status = _status not in (-1, -2, -6)
            logging.error(
                "Get status operation: Something went wrong. Status code %s",
                str(_status))
        except Exception as exc:
            _status = -1
            self.connection_status = False
            logging.error(
                "Get status operation didn't receive operation result from server: %s."
                " Something went wrong. %s", self.server.host, exc)
        return _status

    def load_and_set_coefficients(self):
        dir_name = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(dir_name, "coefficients.txt")
        c_file = c_char_p(filename.encode("utf-8"))
        asa.LoadCoefficients(c_file, self.coefficients)
        try:
            status = asa.SetCoefficients(self.server, self.coefficients)
            assert status >= 0
            self.connection_status = True
        except AssertionError:
            self.connection_status = (status != -1)
            self.logger.error("SetCoefficients failed: %s", str(status))

    def make_measurement(self):
        if not self.server or self.calibrate_state:
            return
        try:
            while self.get_status_operation() > 0:
                time.sleep(0.2)
            assert asa.TriggerMeasurement(self.server) >= 0
            logging.info("Measurement was success!")
        except Exception as exc:
            logging.error("Make measurement: Something went wrong: %s", exc)

    def measure(self) -> Tuple:
        if not self.server or self.calibrate_state:
            return None, None
        iv_curve = asa.IvCurve()
        try:
            asa.GetSettings(self.server, self.asa_settings)
            assert asa.GetIVCurve(self.server, iv_curve, self.asa_settings.number_points) == 0
        except AssertionError:
            self.logger.error("Curve was not received. Something went wrong!")
            return None, None
        except OSError:
            self.logger.error("Curve was not received!")
            return None, None
        self.result = self._recalculate_period_curve(iv_curve)
        return self.settings, self.result

    def set_server_host(self, host: str, port: str):
        """
        Method sets device host.
        :param host: IP address of server;
        :param port: port of server.
        """

        self._host = host
        self._port = port if port else "8888"
        try:
            assert len(self._host) > 0
        except AssertionError:
            self.logger.info("Server host is empty!")
            return
        c_host = c_char_p(self._host.encode("utf-8"))
        c_port = c_char_p(self._port.encode("utf-8"))
        self.server = asa.Server(c_host, c_port)

    def set_settings(self, **kwargs):
        if not self.server:
            return
        for key in self.settings.get_attribute_names():
            if key not in kwargs:
                kwargs[key] = self.settings.get_value(key)
        self.settings = MeasurementSettings(**kwargs)
        self.asa_settings.sampling_rate_hz = c_double(int(self.settings.sampling_rate))
        self.asa_settings.number_points = c_uint32(self.settings.n_points)
        self.asa_settings.number_charge_points = c_uint32(self.settings.n_charge_points)
        self.asa_settings.measure_flags = c_uint32(self.settings.flags)
        self.asa_settings.probe_signal_frequency_hz = c_double(int(
            self.settings.probe_signal_frequency))
        self.asa_settings.voltage_ampl_v = c_double(self.settings.max_voltage)
        self.asa_settings.max_current_m_a = c_double(self.settings.max_current)
        self.asa_settings.debug_model_type = \
            c_uint32(2 * (self.settings.model_type == "Capacitor") +
                     (self.settings.model_type == "Resistor"))
        self.asa_settings.trigger_mode = c_uint32(self.settings.mode == "Manual")
        self.asa_settings.debug_model_nominal = c_double(self.settings.model_nominal)
        try:
            status = asa.SetSettings(self.server, self.asa_settings)
            assert status >= 0
            self.connection_status = True
        except AssertionError:
            self.connection_status = (status != -1)
            self.logger.error("SetSettings failed: %s", str(status))

    def temp_probe(self) -> Tuple[Tuple, Tuple]:
        if not self.server or self.calibrate_state:
            return self.temp_probes
        temp = asa.Temperature()
        try:
            asa.GetTempProbes(self.server, temp)
        except OSError:
            self.logger.error("Temperature of probes were not received!")
            return self.temp_probes
        except AttributeError:
            self.logger.info("Temperature of probes were not received, "
                             "because not connect to server!")
            return self.temp_probes
        self.temp_probes = ((temp.gray_temp, temp.overheat_gray),
                            (temp.blue_temp, temp.overheat_blue))
        return self.temp_probes
