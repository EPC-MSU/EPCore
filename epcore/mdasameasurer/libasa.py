"""
File with library for working with Meridian device functions.
"""

import os
import struct
from ctypes import (Array, byref, c_char_p,  c_double, c_int8, c_size_t,
                    c_ubyte, c_uint32, c_uint8, CDLL, POINTER, Structure)
from platform import system


def _determine_bitness() -> str:
    """
    Function returns bitness of OS.
    :return: bitness.
    """

    if 8 * struct.calcsize("P") == 32:
        return "32"
    return "64"


def _get_path(dir_name: str, file_name: str) -> str:
    """
    Function returns path to file.
    :param dir_name: name of directory in which file is located;
    :param file_name: name of file.
    :return: path.
    """

    base_dir_name = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir_name, dir_name, file_name)


def _get_dll():
    if system() == "Linux":
        return CDLL(_get_path("debian", "libasa.so"))
    elif system() == "Windows":
        bitness = _determine_bitness()
        if bitness == "32":
            return CDLL(_get_path("win32", "asa.dll"))
        raise NotImplementedError(f"Unsupported platform {system()} (64 bit)")
    else:
        raise NotImplementedError(f"Unsupported platform {system()}")


lib = _get_dll()
MAX_NUM_POINTS = 1000
NUM_COMBINATION = 380
_host = "172.16.3.213"
_port = "8888"
HOST = c_char_p(_host.encode("utf-8"))
PORT = c_char_p(_port.encode("utf-8"))


class _IterableStructure(Structure):
    def __iter__(self):
        return (getattr(self, n) for n, t in self._fields_)


def _normalize_arg(value, desired_ctype):
    from collections import Sequence

    if isinstance(value, desired_ctype):
        return value
    elif issubclass(desired_ctype, Array) and isinstance(value, Sequence):
        member_type = desired_ctype._type_

        if desired_ctype._length_ < len(value):
            raise ValueError()

        if issubclass(member_type, c_ubyte) and isinstance(value, bytes):
            return desired_ctype.from_buffer_copy(value)
        elif issubclass(member_type, c_ubyte) and isinstance(value, bytearray):
            return value
        else:
            return desired_ctype(*value)
    else:
        return value


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


def GetLibraryVersion():
    version = lib.GetLibraryVersion
    version.argtype = None
    version.restype = Version
    res = version()
    res.major = _normalize_arg(res.major, c_uint8)
    res.minor = _normalize_arg(res.minor, c_uint8)
    res.bugfix = _normalize_arg(res.bugfix, c_uint8)
    return res.major, res.minor, res.bugfix


def GetAPIVersion():
    version = lib.GetAPIVersion
    version.argtype = None
    version.restype = Version
    res = version()
    res.major = _normalize_arg(res.major, c_uint8)
    res.minor = _normalize_arg(res.minor, c_uint8)
    res.bugfix = _normalize_arg(res.bugfix, c_uint8)
    return res.major, res.minor, res.bugfix


def SetSettings(server, settings):
    lib_func = lib.SetSettings
    lib_func.argtype = Server, AsaSettings
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server), byref(settings)), c_int8)
    return res


def GetSettings(server, settings):
    lib_func = lib.GetSettings
    lib_func.argtype = Server, AsaSettings
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server), byref(settings)), c_int8)
    return res


def GetIVCurve(server, iv_curve, size):
    lib_func = lib.GetIVCurve
    lib_func.argtype = Server, IvCurve, c_uint32
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server), byref(iv_curve), c_uint32(size)), c_int8)
    return res


def TriggerMeasurement(server):
    lib_func = lib.TriggerMeasurement
    lib_func.argtype = Server
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server)), c_int8)
    return res


def Calibrate(server, _type):
    lib_func = lib.Calibrate
    lib_func.argtype = Server, c_uint8
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server), c_uint8(_type)), c_int8)
    return res


def GetStatusButtons(server, button_pressed):
    lib_func = lib.GetStatusButtons
    lib_func.argtype = Server, Buttons
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server), byref(button_pressed)), c_int8)
    return res


def GetTempProbes(server, temperature):
    lib_func = lib.GetTempProbes
    lib_func.argtype = Server, Temperature
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server), byref(temperature)), c_int8)
    return res


def SetMinVC(min_var_v, min_var_c):
    lib_func = lib.SetMinVC
    lib_func.argtype = c_double, c_double
    lib_func(c_double(min_var_v), c_double(min_var_c))


def CompareIvc(first_iv_curve, second_iv_curve):
    lib_func = lib.CompareIVC
    lib_func.argtype = POINTER(c_double), POINTER(c_double), c_size_t, POINTER(c_double), POINTER(c_double), c_size_t
    lib_func.restype = c_double
    res = lib_func(first_iv_curve.voltages, first_iv_curve.currents, len(first_iv_curve.voltages),
                   second_iv_curve.voltages, second_iv_curve.currents, len(second_iv_curve.voltages))
    res = _normalize_arg(res, c_double)
    return res


def GetNumberPointsForSinglePeriod(settings):
    lib_func = lib.GetNumberPointsForSinglePeriod
    lib_func.argtype = AsaSettings
    lib_func.restype = c_uint32
    res = _normalize_arg(lib_func(byref(settings)), c_uint32)
    return res


def GetLastOperationResult(server):
    lib_func = lib.GetLastOperationResult
    lib_func.argtype = Server
    lib_func.restype = c_int8
    res = lib_func(byref(server))
    return res


def LoadCoefficients(file_name, coefficients):
    lib_func = lib.LoadCoefficientTable
    lib_func.argtype = c_char_p, AsaCoefficients
    lib_func.restype = None
    lib_func(file_name, byref(coefficients))


def SaveCoefficients(file_name, coefficients):
    lib_func = lib.SaveCoefficientTable
    lib_func.argtype = c_char_p, AsaCoefficients
    lib_func.restype = None
    lib_func(file_name, byref(coefficients))


def SetCoefficients(server, coefficients):
    lib_func = lib.SetCoefficients
    lib_func.argtype = Server, AsaCoefficients
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server), byref(coefficients)), c_int8)
    return res


def GetCoefficients(server, coefficients):
    lib_func = lib.GetCoefficients
    lib_func.argtype = Server, AsaCoefficients
    lib_func.restype = c_int8
    res = _normalize_arg(lib_func(byref(server), byref(coefficients)), c_int8)
    return res


if __name__ == "__main__":

    server = Server(HOST, PORT)
    coef = AsaCoefficients()
    dir_name = os.path.dirname(os.path.abspath(__file__))
    file_name = os.path.join(dir_name, "coefficients.txt")
    LoadCoefficients(c_char_p(file_name.encode("utf-8")), coef)
    SetCoefficients(server, coef)
    settings = AsaSettings()
    settings.sampling_rate_hz = c_double(10000)
    settings.number_points = c_uint32(100)
    settings.number_charge_points = c_uint32(400)
    settings.measure_flags = c_uint32(0)
    settings.probe_signal_frequency_hz = c_double(100)
    settings.voltage_ampl_v = c_double(5)
    settings.max_current_m_a = c_double(5)
    settings.debug_model_type = c_uint32(1)
    settings.debug_model_nominal = c_double(100)
    settings.trigger_mode = c_uint32(0)
    SetSettings(server, settings)
    iv_curve = IvCurve()
    status = GetIVCurve(server, iv_curve, settings.number_points)
    settings.voltage_ampl_v = c_double(15)
    SetSettings(server, settings)
    ivc_curve = IvCurve()
    # status = CalibrateVoltage(server)
    status = GetIVCurve(server, ivc_curve, settings.number_points)
    SetMinVC(0, 0)
    f = CompareIvc(iv_curve, ivc_curve)
    temp = Temperature()
    button_pressed = Buttons()
    GetStatusButtons(server, button_pressed)
    GetTempProbes(server, temp)
    n_p = GetNumberPointsForSinglePeriod(settings)
    print("N_P: {}\n".format(n_p))
    print(temp.overheat_blue, button_pressed.gray_button)
    # print(f)
    # for i in range(settings.number_points):
    #     print(iv_curve.currents[i], iv_curve.voltages[i])
