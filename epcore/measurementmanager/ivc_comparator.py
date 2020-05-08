from ctypes import CDLL, c_double, c_size_t, POINTER
from platform import system
from ..elements import IVCurve


def _fullpath_lib(name: str) -> str:
    from os.path import dirname, join
    return join(dirname(__file__), name)


def _get_dll():
    if system() == "Linux":
        return CDLL(_fullpath_lib("libivcmp.so"))
    elif system() == "Windows":
        return CDLL(_fullpath_lib("ivcmp.dll"))
    else:
        raise NotImplementedError("Unsupported platform {0}".format(system()))


class IVCComparator:
    voltage_amplitude = 12.
    r_cs = 475.
    current_amplitude = (voltage_amplitude / r_cs * 1000)
    max_num_points = 10

    def __init__(self):
        self._lib = _get_dll()

        self._lib.SetMinVC.argtype = c_double, c_double

        self._lib.CompareIVC.argtype = POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double), \
                                       c_size_t
        self._lib.CompareIVC.restype = c_double

    def set_min_ivc(self, min_var_v: float, min_var_c: float):
        self._lib.SetMinVC(min_var_v, min_var_c)

    def compare_ivc(self, first_ivc: IVCurve, second_ivc: IVCurve) -> float:
        res = self._lib.CompareIVC(first_ivc.voltages, first_ivc.currents, second_ivc.voltages, second_ivc.currents,
                                   len(first_ivc.voltages))
        return float(res)
