import time
from collections import Sequence
from ctypes import (Array, byref, c_char_p, c_double, c_int8, c_size_t, c_ubyte, c_uint32, c_uint8,
                    CDLL, POINTER, Structure)
from os.path import abspath, dirname, join
from platform import system
from typing import Callable


def _get_full_path(name: str) -> str:
    """
    Function returns full path to file with given name.
    :param name: name of file.
    :return: full path to file.
    """

    return join(dirname(abspath(__file__)), name)


def get_dll() -> CDLL:
    """
    Function returns library to work with ASA device.
    :return: ASA library.
    """

    if system() == "Linux":
        return CDLL("libasa.so")
    if system() == "Windows":
        return CDLL(_get_full_path("libasa-win32/asa.dll"))
    raise NotImplementedError("Unsupported platform {}".format(system()))


MAX_NUM_POINTS = 1000
NUM_COMBINATION = 380
HOST = c_char_p("172.16.128.137".encode("utf-8"))
PORT = c_char_p("8888".encode("utf-8"))


class _IterableStructure(Structure):
    def __iter__(self):
        return (getattr(self, n) for n, t in self._fields_)


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


class AsaResponseStatus:
    """
    Class with status values from ASA device response.
    """

    ASA_OK = 0
    ASA_IN_PROGRESS = 1
    SERVER_RESPONSE_ERROR = -1
    INTERNAL_SERVER_ERROR = -2
    ASA_VALUE_ERROR = -3
    ASA_TYPE_ERROR = -4
    ASA_FORMAT_ERROR = -5
    ASA_CONNECTION_ERROR = -6

    @classmethod
    def get_errors(cls) -> tuple:
        """
        Method returns status values that indicate problems with connection
        to server.
        :return: status values.
        """

        return cls.ASA_CONNECTION_ERROR, cls.SERVER_RESPONSE_ERROR


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
        if status == AsaResponseStatus.ASA_CONNECTION_ERROR:
            raise AsaConnectionError
        if status == AsaResponseStatus.ASA_FORMAT_ERROR:
            raise AsaFormatError
        if status == AsaResponseStatus.INTERNAL_SERVER_ERROR:
            raise AsaInternalServerError
        if status == AsaResponseStatus.SERVER_RESPONSE_ERROR:
            raise AsaServerResponseError
        if status == AsaResponseStatus.ASA_TYPE_ERROR:
            raise AsaTypeError
        if status == AsaResponseStatus.ASA_VALUE_ERROR:
            raise AsaValueError
        return status
    return wrapper


class Version(_IterableStructure):
    _fields_ = (
        ("major", c_uint8),
        ("minor", c_uint8),
        ("bugfix", c_uint8)
     )


class Server(_IterableStructure):
    _fields_ = (
          ("host", c_char_p),
          ("port", c_char_p)
    )


class Buttons(_IterableStructure):
    _fields_ = (
        ("gray_button", c_uint32),
        ("blue_button", c_uint32)
    )


class Temperature(_IterableStructure):
    _fields_ = (
        ("gray_temp", c_uint32),
        ("blue_temp", c_uint32),
        ("overheat_gray", c_uint32),
        ("overheat_blue", c_uint32)
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


class IvCurve(_IterableStructure):
    _fields_ = (
        ("voltages", c_double * MAX_NUM_POINTS),
        ("currents", c_double * MAX_NUM_POINTS),
        ("length", c_size_t)
    )

    def __init__(self):
        self.length = MAX_NUM_POINTS


def GetLibraryVersion(lib: CDLL):
    version = lib.GetLibraryVersion
    version.argtype = None
    version.restype = Version
    res = version()
    res.major = _normalize_arg(res.major, c_uint8)
    res.minor = _normalize_arg(res.minor, c_uint8)
    res.bugfix = _normalize_arg(res.bugfix, c_uint8)
    return res.major, res.minor, res.bugfix


def GetAPIVersion(lib: CDLL):
    version = lib.GetAPIVersion
    version.argtype = None
    version.restype = Version
    res = version()
    res.major = _normalize_arg(res.major, c_uint8)
    res.minor = _normalize_arg(res.minor, c_uint8)
    res.bugfix = _normalize_arg(res.bugfix, c_uint8)
    return res.major, res.minor, res.bugfix


@check_exception
def SetSettings(lib: CDLL, server: Server, settings: AsaSettings) -> int:
    lib_func = lib.SetSettings
    lib_func.argtype = Server, AsaSettings
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server), byref(settings)), c_int8)
    return res


@check_exception
def GetSettings(lib: CDLL, server: Server, settings: AsaSettings) -> int:
    lib_func = lib.GetSettings
    lib_func.argtype = Server, AsaSettings
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server), byref(settings)), c_int8)
    return res


@check_exception
def GetIVCurve(lib: CDLL, server: Server, iv_curve: IvCurve, size: c_uint32) -> int:
    lib_func = lib.GetIVCurve
    lib_func.argtype = Server, IvCurve, c_uint32
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server), byref(iv_curve), c_uint32(size)), c_int8)
    return res


@check_exception
def TriggerMeasurement(lib: CDLL, server: Server) -> int:
    lib_func = lib.TriggerMeasurement
    lib_func.argtype = Server
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server)), c_int8)
    return res


@check_exception
def Calibrate(lib: CDLL, server: Server, calibration_type: int) -> int:
    lib_func = lib.Calibrate
    lib_func.argtype = Server, c_uint8
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server), c_uint8(calibration_type)), c_int8)
    return res


@check_exception
def GetStatusButtons(lib: CDLL, server: Server, button_pressed: Buttons) -> int:
    lib_func = lib.GetStatusButtons
    lib_func.argtype = Server, Buttons
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server), byref(button_pressed)), c_int8)
    return res


@check_exception
def GetTempProbes(lib: CDLL, server: Server, temperature: Temperature) -> int:
    lib_func = lib.GetTempProbes
    lib_func.argtype = Server, Temperature
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server), byref(temperature)), c_int8)
    return res


def SetMinVC(lib, min_var_v, min_var_c):
    lib_func = lib.SetMinVC
    lib_func.argtype = c_double, c_double
    lib_func(c_double(min_var_v), c_double(min_var_c))


def CompareIvc(lib, first_iv_curve, second_iv_curve):
    lib_func = lib.CompareIVC
    lib_func.argtype = (POINTER(c_double), POINTER(c_double), c_size_t, POINTER(c_double),
                        POINTER(c_double), c_size_t)
    lib_func.restype = c_double
    res = lib_func(first_iv_curve.voltages, first_iv_curve.currents, len(first_iv_curve.voltages),
                   second_iv_curve.voltages, second_iv_curve.currents,
                   len(second_iv_curve.voltages))
    res = _normalize_arg(res, c_double)
    return res


@check_exception
def GetNumberPointsForSinglePeriod(lib: CDLL, settings: AsaSettings) -> int:
    lib_func = lib.GetNumberPointsForSinglePeriod
    lib_func.argtype = AsaSettings
    lib_func.restype = c_uint32
    res = _normalize_arg(lib_func(byref(settings)), c_uint32)
    return res


def GetLastOperationResult(lib: CDLL, server: Server) -> int:
    lib_func = lib.GetLastOperationResult
    lib_func.argtype = Server
    lib_func.restype = c_int8
    res = lib_func(byref(server))
    return res


def LoadCoefficients(lib: CDLL, file_name: c_char_p, coefficients: AsaCoefficients):
    lib_func = lib.LoadCoefficientTable
    lib_func.argtype = c_char_p, AsaCoefficients
    lib_func.restype = None
    lib_func(file_name, byref(coefficients))


def SaveCoefficients(lib: CDLL, file_name: c_char_p, coefficients: AsaCoefficients):
    lib_func = lib.SaveCoefficientTable
    lib_func.argtype = c_char_p, AsaCoefficients
    lib_func.restype = None
    lib_func(file_name, byref(coefficients))


@check_exception
def SetCoefficients(lib: CDLL, server: Server, coefficients: AsaCoefficients) -> int:
    lib_func = lib.SetCoefficients
    lib_func.argtype = Server, AsaCoefficients
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server), byref(coefficients)), c_int8)
    return res


@check_exception
def GetCoefficients(lib: CDLL, server: Server, coefficients: AsaCoefficients) -> int:
    lib_func = lib.GetCoefficients
    lib_func.argtype = Server, AsaCoefficients
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server), byref(coefficients)), c_int8)
    return res


if __name__ == "__main__":

    def wait_finish(lib: CDLL):
        while GetLastOperationResult(lib, server) != AsaResponseStatus.ASA_OK:
            time.sleep(0.2)

    local_lib = get_dll()
    server = Server(HOST, PORT)
    settings_from_device = AsaSettings()

    GetSettings(local_lib, server, settings_from_device)
    wait_finish(local_lib)
    print(settings_from_device.sampling_rate_hz)
    print(settings_from_device.debug_model_nominal)

    settings = AsaSettings()
    settings.sampling_rate_hz = c_double(10000)
    settings.number_points = c_uint32(100)
    settings.number_charge_points = c_uint32(400)
    settings.measure_flags = c_uint32(0)
    settings.probe_signal_frequency_hz = c_double(100)
    settings.voltage_ampl_v = c_double(5)
    settings.max_current_m_a = c_double(5)
    settings.debug_model_type = c_uint32(1)
    settings.debug_model_nominal = c_double(0.20)
    settings.trigger_mode = c_uint32(0)
    SetSettings(local_lib, server, settings)
    wait_finish(local_lib)

    GetSettings(local_lib, server, settings_from_device)
    wait_finish(local_lib)
    print(settings_from_device.sampling_rate_hz)
    print(settings_from_device.debug_model_nominal)

    settings.debug_model_nominal = c_double(12783)
    SetSettings(local_lib, server, settings)
    wait_finish(local_lib)

    GetSettings(local_lib, server, settings_from_device)
    wait_finish(local_lib)

    print(settings_from_device.debug_model_nominal)

    iv_curve = IvCurve()
    status = GetIVCurve(local_lib, server, iv_curve, settings.number_points)
    settings.voltage_ampl_v = c_double(15)
    SetSettings(local_lib, server, settings)
    ivc_curve = IvCurve()
    # status = CalibrateVoltage(server)
    status = GetIVCurve(local_lib, server, ivc_curve, settings.number_points)
    SetMinVC(local_lib, 0, 0)
    f = CompareIvc(local_lib, iv_curve, ivc_curve)
    temp = Temperature()
    button_pressed = Buttons()
    GetStatusButtons(local_lib, server, button_pressed)
    GetTempProbes(local_lib, server, temp)
    n_p = GetNumberPointsForSinglePeriod(local_lib, settings)
    print("N_P: {}\n".format(n_p))
    print(temp.overheat_blue, button_pressed.gray_button)
