import os
import struct
from ctypes import Array, c_double, c_size_t, CDLL, POINTER
from platform import system, uname
from typing import List
from ..elements import IVCurve


def get_full_path(name: str) -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)


def get_dll() -> CDLL:
    os_kind = system().lower()
    if os_kind == "windows":
        if 8 * struct.calcsize("P") == 32:
            lib = CDLL(get_full_path(os.path.join("ivcmp-win32", "ivcmp.dll")))
        else:
            lib = CDLL(get_full_path(os.path.join("ivcmp-win64", "ivcmp.dll")))
    elif os_kind == "freebsd" or "linux" in os_kind:
        if uname()[4] == "aarch64":
            lib = CDLL(get_full_path(os.path.join("ivcmp-arm64", "libivcmp.so")))
        else:
            lib = CDLL(get_full_path(os.path.join("ivcmp-debian", "libivcmp.so")))
    else:
        raise NotImplementedError("Unsupported platform {}".format(os_kind))
    return lib


def _to_c_array(arr: List[float]) -> Array:
    return (c_double * len(arr))(*arr)


class IVCComparator:

    voltage_amplitude = 12.
    r_cs = 475.
    current_amplitude = (voltage_amplitude / r_cs * 1000)
    max_num_points = 10

    def __init__(self) -> None:
        self._lib = get_dll()
        self._lib.SetMinVarVC.argtype = c_double, c_double
        self._lib.CompareIVC.argtype = (POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double),
                                        c_size_t)
        self._lib.CompareIVC.restype = c_double

    def compare_ivc(self, first_ivc: IVCurve, second_ivc: IVCurve) -> float:
        res = self._lib.CompareIVC(_to_c_array(first_ivc.voltages), _to_c_array(first_ivc.currents),
                                   len(first_ivc.voltages), _to_c_array(second_ivc.voltages),
                                   _to_c_array(second_ivc.currents), len(second_ivc.voltages))
        return float(res)

    def set_min_ivc(self, min_var_v: float, min_var_c: float) -> None:
        self._lib.SetMinVarVC(c_double(min_var_v), c_double(min_var_c))
