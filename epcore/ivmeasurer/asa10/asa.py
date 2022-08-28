import os
import struct
import sys
import time
from collections import Sequence
from ctypes import (Array, byref, c_char_p, c_double, c_int8, c_size_t, c_ubyte, c_uint32, c_uint8, CDLL, cdll,
                    POINTER, Structure)
from platform import system
from typing import Callable, Iterable, Tuple


COMPONENT_MODEL_TYPE_NONE = 0  # undefined type
COMPONENT_MODEL_TYPE_RESISTOR = 1  # resistor
COMPONENT_MODEL_TYPE_CAPACITOR = 2  # capacitor

MODE_AUTO = 0  # automatic start of measurements
MODE_MANUAL = 1  # manual start of measurements

ASA_OK = 0  # everything works normally
ASA_IN_PROGRESS = 1  # operation in progress
SERVER_RESPONSE_ERROR = -1  # incorrect server response
INTERNAL_SERVER_ERROR = -2  # error occurred while executing the function on the server
ASA_VALUE_ERROR = -3  # server received value out of range
ASA_TYPE_ERROR = -4  # server received value with the wrong type
ASA_FORMAT_ERROR = -5  # server received value with incorrect format or not received at all
ASA_CONNECTION_ERROR = -6  # server failed to connect to device

FAST_CLOSE_CALIBRATE = 0  # starting calibration for given set of parameters with closed probes
FAST_OPEN_CALIBRATE = 1  # starting calibration for given set of parameters with open probes
FAST_CLOSE_CALIBRATE_AND_SAVE = 2  # starting calibration for given set of parameters with closed probes,
# saving result to device
FAST_OPEN_CALIBRATE_AND_SAVE = 3  # starting calibration for given set of parameters with open probes,
# saving result to device
FULL_CLOSE_CALIBRATE_AND_SAVE = 4  # starting calibration for all parameters with closed probes,
# saving results to device
FULL_OPEN_CALIBRATE_AND_SAVE = 5  # starting calibration for all parameters with open probes,
# saving results to device

MIN_VAR_V_DEFAULT = 0.6
MIN_VAR_C_DEFAULT = 0.0002
N_POINTS = 512
MAX_NUM_POINTS = 1000
NUM_COMBINATION = 380

ADDITIONAL_LIBRARIES_FOR_LINUX: Tuple[str] = ("libxmlrpc_util.so.4.51", "libxmlrpc.so.3.51", "libxmlrpc_client.so.3.51",
                                              "libxmlrpc_xmlparse.so.3.51", "libxmlrpc_xmltok.so.3.51")
ADDITIONAL_LIBRARIES_FOR_WINDOWS: Tuple[str] = ("libxmlrpc_util.dll", "libxmlrpc_xmltok.dll", "libxmlrpc_xmlparse.dll",
                                                "libxmlrpc.dll", "libxmlrpc_client.dll")


class AsaConnectionError(Exception):
    pass


class AsaFormatError(Exception):
    pass


class AsaInternalServerError(Exception):
    pass


class AsaServerResponseError(Exception):
    pass


class AsaTypeError(Exception):
    pass


class AsaValueError(Exception):
    pass


def check_exception(func: Callable):
    """
    Decorator for checking if exception is thrown.
    :param func: decorated function.
    """

    def wrapper(*args, **kwargs):
        status = func(*args, **kwargs)
        if status == ASA_CONNECTION_ERROR:
            raise AsaConnectionError
        if status == ASA_FORMAT_ERROR:
            raise AsaFormatError
        if status == INTERNAL_SERVER_ERROR:
            raise AsaInternalServerError
        if status == SERVER_RESPONSE_ERROR:
            raise AsaServerResponseError
        if status == ASA_TYPE_ERROR:
            raise AsaTypeError
        if status == ASA_VALUE_ERROR:
            raise AsaValueError
        return status
    return wrapper


class _IterableStructure(Structure):
    def __iter__(self):
        return (getattr(self, n) for n, t in self._fields_)


class AsaCoefficients(_IterableStructure):
    _fields_ = (
        ("probe_freq_array", c_double * NUM_COMBINATION),
        ("voltage_ampl_array", c_double * NUM_COMBINATION),
        ("max_current_array", c_double * NUM_COMBINATION),
        ("limit_resistor_array", c_uint32 * NUM_COMBINATION),
        ("sense_resistor_array", c_uint32 * NUM_COMBINATION),
        ("cur_calibration_array", c_uint32 * NUM_COMBINATION),
        ("volt_calibration_array", c_uint32 * NUM_COMBINATION),
        ("cur_calibration_kz_array", c_uint32 * NUM_COMBINATION),
        ("volt_calibration_kz_array", c_uint32 * NUM_COMBINATION)
    )


class AsaSettings(_IterableStructure):
    _fields_ = (
        ("sampling_rate_hz", c_double),
        ("probe_signal_frequency_hz", c_double),
        ("number_points", c_uint32),
        ("number_charge_points", c_uint32),
        ("voltage_ampl_v", c_double),
        ("max_current_m_a", c_double),
        ("measure_flags", c_uint32),
        ("debug_model_type", c_uint32),
        ("debug_model_nominal", c_double),
        ("trigger_mode", c_uint32)
    )


class Buttons(_IterableStructure):
    _fields_ = (
        ("gray_button", c_uint32),
        ("blue_button", c_uint32)
    )


class IVCurve(_IterableStructure):
    _fields_ = (
        ("voltages", c_double * MAX_NUM_POINTS),
        ("currents", c_double * MAX_NUM_POINTS),
        ("length", c_size_t)
    )

    def __init__(self):
        self.length = MAX_NUM_POINTS


IvCurve = IVCurve  # to maintain compatibility with previous versions


class Server(_IterableStructure):
    _fields_ = (
        ("host", c_char_p),
        ("port", c_char_p)
    )


class Temperature(_IterableStructure):
    _fields_ = (
        ("gray_temp", c_uint32),
        ("blue_temp", c_uint32),
        ("overheat_gray", c_uint32),
        ("overheat_blue", c_uint32)
    )


class Version(_IterableStructure):
    _fields_ = (
        ("major", c_uint8),
        ("minor", c_uint8),
        ("bugfix", c_uint8)
    )


def _check_status(server: Server, status: int, func_name: str):
    """
    Function writes information about last operation with server.
    :param server: server with measuring device;
    :param status: status of last operation;
    :param func_name: name of last operation.
    """

    wait_iter = 0
    while status == ASA_IN_PROGRESS:
        if wait_iter == 0:
            print("Operation is in progress")
        elif wait_iter % 10 == 0:
            print(".")
        wait_iter += 1
        status = GetLastOperationResult(server)
        if status == ASA_OK:
            print("\n{} is done!\n".format(func_name))
            break
        elif status != ASA_IN_PROGRESS and status != ASA_OK:
            print("")
            break
    if status == ASA_CONNECTION_ERROR:
        print("ConnectionError during {} call. ConnectionError code: {}".format(func_name, status))
        sys.exit(-1)
    elif status < ASA_OK:
        print("Error during {} call. Error code: {}".format(func_name, status))
        sys.exit(-1)


def _get_dll() -> CDLL:
    """
    Function returns loaded library.
    :return: loaded libasa library.
    """

    if system() == "Linux":
        libraries = [_get_full_path(os.path.join("libasa-debian", library))
                     for library in ADDITIONAL_LIBRARIES_FOR_WINDOWS]
        _load_additional_libraries(libraries)
        return CDLL(_get_full_path(os.path.join("libasa-debian", "libasa.so")))
    if system() == "Windows":
        if 8 * struct.calcsize("P") == 32:
            libraries = [_get_full_path(os.path.join("libasa-win32", library))
                         for library in ADDITIONAL_LIBRARIES_FOR_WINDOWS]
            _load_additional_libraries(libraries)
            return CDLL(_get_full_path(os.path.join("libasa-win32", "asa.dll")))
        libraries = [_get_full_path(os.path.join("libasa-win64", library))
                     for library in ADDITIONAL_LIBRARIES_FOR_WINDOWS]
        _load_additional_libraries(libraries)
        return CDLL(_get_full_path(os.path.join("libasa-win64", "asa.dll")))
    raise NotImplementedError("Unsupported platform {}".format(system()))


def _get_full_path(name: str) -> str:
    """
    Function returns path to file with given name.
    :param name: name of file.
    :return: path to file.
    """

    return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)


def _load_additional_libraries(libraries: Iterable[str]):
    """
    Function loads additional libraries with given names.
    :param libraries: tuple with names of additional libraries to load.
    """

    for library in libraries:
        cdll.LoadLibrary(library)


def _normalize_arg(value, desired_ctype):
    if isinstance(value, desired_ctype):
        return value
    if issubclass(desired_ctype, Array) and isinstance(value, Sequence):
        member_type = desired_ctype._type_
        if desired_ctype._length_ < len(value):
            raise ValueError()
        if issubclass(member_type, c_ubyte) and isinstance(value, bytes):
            return desired_ctype.from_buffer_copy(value)
        if issubclass(member_type, c_ubyte) and isinstance(value, bytearray):
            return value
        return desired_ctype(*value)
    return value


lib = _get_dll()
HOST = c_char_p("172.16.128.137".encode("utf-8"))
PORT = c_char_p("8888".encode("utf-8"))


def Calibrate(server: Server, calibration_type: int) -> int:
    """
    Function calibrates measuring device on server.
    :param server: server;
    :param calibration_type: type of calibration to be performed.
    :return: status of operation.
    """

    lib_func = lib.Calibrate
    lib_func.argtype = Server, c_uint8
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server), c_uint8(calibration_type)), c_int8)
    return res


def CompareIVC(first_iv_curve: IVCurve, second_iv_curve: IVCurve) -> float:
    """
    Function compares two IV-curves.
    :param first_iv_curve: first IV-curve;
    :param second_iv_curve: second IV-curve.
    :return: degree of difference.
    """

    lib_func = lib.CompareIVC
    lib_func.argtype = POINTER(c_double), POINTER(c_double), c_size_t, POINTER(c_double), POINTER(c_double), c_size_t
    lib_func.restype = c_double
    res = lib_func(first_iv_curve.voltages, first_iv_curve.currents, len(first_iv_curve.voltages),
                   second_iv_curve.voltages, second_iv_curve.currents, len(second_iv_curve.voltages))
    res = _normalize_arg(res, c_double)
    return res


CompareIvc = CompareIVC  # to maintain compatibility with previous versions


def GetAPIVersion() -> Tuple[int, int, int]:
    """
    Function returns API version.
    :return: tuple with major, minor and bugfix values of version.
    """

    version = lib.GetAPIVersion
    version.argtype = None
    version.restype = Version
    res = version()
    res.major = _normalize_arg(res.major, c_uint8)
    res.minor = _normalize_arg(res.minor, c_uint8)
    res.bugfix = _normalize_arg(res.bugfix, c_uint8)
    return res.major, res.minor, res.bugfix


def GetCoefficients(server: Server, coefficients: AsaCoefficients) -> int:
    """
    Function reads calibration coefficients on measuring device from server and
    writes to AsaCoefficients object.
    :param server: server;
    :param coefficients: object to write coefficients.
    :return: status of operation.
    """

    lib_func = lib.GetCoefficients
    lib_func.argtype = Server, AsaCoefficients
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server), byref(coefficients)), c_int8)
    return res


def GetIVCurve(server: Server, iv_curve: IVCurve, size: int) -> int:
    """
    Function reads IV-curve from server and saves to IVCurve object.
    :param server: server;
    :param iv_curve: object to write IV-curve;
    :param size: number of point in required IV-curve.
    :return: status of operation.
    """

    lib_func = lib.GetIVCurve
    lib_func.argtype = Server, IVCurve, c_uint32
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server), byref(iv_curve), c_uint32(size)), c_int8)
    return res


def GetLastOperationResult(server: Server) -> int:
    """
    Function returns status of last operation.
    :param server: server.
    :return: status of last operation.
    """

    lib_func = lib.GetLastOperationResult
    lib_func.argtype = Server
    lib_func.restype = c_int8
    res = lib_func(byref(server))
    return res


def GetLibraryVersion() -> Tuple[int, int, int]:
    """
    Function returns libasa library version.
    :return: tuple with major, minor and bugfix values of version.
    """

    version = lib.GetLibraryVersion
    version.argtype = None
    version.restype = Version
    res = version()
    res.major = _normalize_arg(res.major, c_uint8)
    res.minor = _normalize_arg(res.minor, c_uint8)
    res.bugfix = _normalize_arg(res.bugfix, c_uint8)
    return res.major, res.minor, res.bugfix


def GetNumberPointsForSinglePeriod(settings: AsaSettings) -> int:
    """
    Function returns number of points for single period.
    :param settings: measurement settings.
    :return: number of points for single period.
    """

    lib_func = lib.GetNumberPointsForSinglePeriod
    lib_func.argtype = AsaSettings
    lib_func.restype = c_uint32
    res = _normalize_arg(lib_func(byref(settings)), c_uint32)
    return res


def GetSettings(server: Server, settings: AsaSettings) -> int:
    """
    Function reads measurement settings from server and saves to AsaSettings object.
    :param server: server;
    :param settings: object to write measurement settings.
    :return: status of operation.
    """

    lib_func = lib.GetSettings
    lib_func.argtype = Server, AsaSettings
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server), byref(settings)), c_int8)
    return res


def GetStatusButtons(server: Server, button_pressed: Buttons) -> int:
    """
    Function reads statuses of buttons on gray and blue probes from server.
    :param server: server;
    :param button_pressed: object to write statuses of buttons.
    :return: status of operation.
    """

    lib_func = lib.GetStatusButtons
    lib_func.argtype = Server, Buttons
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server), byref(button_pressed)), c_int8)
    return res


def GetTempProbes(server: Server, temperature: Temperature) -> int:
    """
    Function reads temperatures of gray and blue probes from server.
    :param server: server;
    :param temperature: object to write temperatures of probes.
    :return: status of operation.
    """

    lib_func = lib.GetTempProbes
    lib_func.argtype = Server, Temperature
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server), byref(temperature)), c_int8)
    return res


def LoadCoefficients(file_name: str, coefficients: AsaCoefficients):
    """
    Function reads calibration coefficients from file.
    :param file_name: name of file with calibration coefficients;
    :param coefficients: object to write calibration coefficients.
    """

    lib_func = lib.LoadCoefficientTable
    lib_func.argtype = c_char_p, AsaCoefficients
    lib_func.restype = None
    lib_func(file_name, byref(coefficients))


def SetSettings(server: Server, settings: AsaSettings) -> int:
    """
    Function writes measurement settings to device.
    :param server: server;
    :param settings: measurement settings.
    :return: status of operation.
    """

    lib_func = lib.SetSettings
    lib_func.argtype = Server, AsaSettings
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server), byref(settings)), c_int8)
    return res


def SaveCoefficients(file_name: str, coefficients: AsaCoefficients):
    """
    Function writes calibration coefficients to file.
    :param file_name: name of file to save coefficients;
    :param coefficients: calibration coefficients.
    """

    lib_func = lib.SaveCoefficientTable
    lib_func.argtype = c_char_p, AsaCoefficients
    lib_func.restype = None
    lib_func(file_name, byref(coefficients))


def SetMinVarVC(min_var_v: float, min_var_c: float):
    """
    Function sets noise amplitudes of voltage and current to correctly compare IV-curves.
    :param min_var_v: amplitude of voltage;
    :param min_var_c: amplitude of current.
    """

    lib_func = lib.SetMinVarVC
    lib_func.argtype = c_double, c_double
    lib_func(c_double(min_var_v), c_double(min_var_c))


SetMinVC = SetMinVarVC  # to maintain compatibility with previous versions


def SetCoefficients(server: Server, coefficients: AsaCoefficients) -> int:
    """
    Function writes calibration coefficients to device.
    :param server: server;
    :param coefficients: calibration coefficients.
    :return: status of operation.
    """

    lib_func = lib.SetCoefficients
    lib_func.argtype = Server, AsaCoefficients
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server), byref(coefficients)), c_int8)
    return res


def TriggerMeasurement(server: Server) -> int:
    """
    Function starts measurements on server.
    :param server: server.
    :return: status of operation.
    """

    lib_func = lib.TriggerMeasurement
    lib_func.argtype = Server
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server)), c_int8)
    return res


if __name__ == "__main__":
    if len(sys.argv) < 2:
        host = input("Enter ASA device IP address (format: 192.168.1.1): ")
    else:
        host = sys.argv[1]
    host = c_char_p(host.encode("utf-8"))
    server = Server(host, PORT)

    print("Using libasa {}".format(".".join(list(map(str, GetLibraryVersion())))))
    print("Using API {}".format(".".join(list(map(str, GetAPIVersion())))))
    print("-- Update device settings --")
    settings = AsaSettings()
    settings.sampling_rate_hz = c_double(10000)
    settings.number_points = c_uint32(N_POINTS)
    settings.number_charge_points = c_uint32(N_POINTS)
    settings.probe_signal_frequency_hz = c_double(100)
    settings.voltage_ampl_v = c_double(1)
    settings.max_current_m_a = c_double(10)
    settings.measure_flags = c_uint32(0)
    settings.debug_model_type = c_uint32(COMPONENT_MODEL_TYPE_CAPACITOR)
    settings.debug_model_nominal = c_double(0.00000001)
    settings.trigger_mode = c_uint32(MODE_MANUAL)
    status = SetSettings(server, settings)
    _check_status(server, status, "SetSettings")

    print("-- Read settings from device --")
    settings_in = AsaSettings()
    status = GetSettings(server, settings_in)
    _check_status(server, status, "GetSettings")

    print("-- Do fast calibration with open probes --")
    status = Calibrate(server, FAST_OPEN_CALIBRATE)
    _check_status(server, status, "Calibrate")
    if status < 0:
        print("Calibration was not started")
        sys.exit(1)
    while GetLastOperationResult(server) == ASA_OK:
        time.sleep(0.5)
    while GetLastOperationResult(server) == ASA_IN_PROGRESS:
        time.sleep(0.5)
    if GetLastOperationResult(server) == ASA_OK:
        print("Calibration completed successfully")
    else:
        print("Calibration completed unsuccessfully")

    print("-- Do measure IV curve --")
    status = TriggerMeasurement(server)
    while GetLastOperationResult(server) != ASA_OK:
        time.sleep(0.5)
    _check_status(server, status, "TriggerMeasurement")

    print("-- Get measured IV curve --")
    iv_curve = IVCurve()
    status = GetIVCurve(server, iv_curve, settings.number_points)
    _check_status(server, status, "GetIVCurve")

    print("-- Get status of buttons --")
    buttons = Buttons()
    status = GetStatusButtons(server, buttons)
    _check_status(server, status, "GetStatusButtons")

    print("-- Get temperature of probes --")
    temperature = Temperature()
    status = GetTempProbes(server, temperature)
    _check_status(server, status, "GetTempProbes")

    print("Got settings (Out, In):")
    print("Probe signal frequency: ({:.1f}, {:.1f}) Hz".format(settings.probe_signal_frequency_hz,
                                                               settings_in.probe_signal_frequency_hz))
    print("Voltage amplitude: ({:.1f}, {:.1f}) V".format(settings.voltage_ampl_v, settings_in.voltage_ampl_v))
    print("Number of points: ({}, {})".format(settings.number_points, settings_in.number_points))
    print("Maximum current: ({:.1f}, {:.1f}) mA".format(settings.max_current_m_a, settings_in.max_current_m_a))
    print("Virtual component model: ({}, {})".format(settings.debug_model_type, settings_in.debug_model_type))
    print("Virtual component model nominal: ({}, {})".format(settings.debug_model_nominal,
                                                             settings_in.debug_model_nominal))
    print("Virtual component model: ({}, {})".format(settings.trigger_mode, settings_in.trigger_mode))
    print("ButtonPressed: ({}, {})".format(buttons.gray_button, buttons.blue_button))
    print("Temperature: ({}, {}, {}, {})".format(temperature.overheat_gray, temperature.gray_temp,
                                                 temperature.overheat_blue, temperature.blue_temp))
    print("-- Get number of points for one period of curve --")
    num_points_to_print = GetNumberPointsForSinglePeriod(settings_in)
    print("Number of points for one period of curve: {}".format(num_points_to_print))
    print("Voltages (V) and currents (A) of received curve:")
    for i in range(num_points_to_print):
        print("[{:.4f}, {:.4f}];".format(iv_curve.voltages[i], iv_curve.currents[i]))

    print("-- Set default values as threshold of noise for compare curves --")
    SetMinVarVC(MIN_VAR_V_DEFAULT, MIN_VAR_C_DEFAULT)

    print("-- Comparison of two identical curves must be 0 --")
    score = CompareIVC(iv_curve, iv_curve)
    print("Score = {}".format(score))
