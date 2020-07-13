import numpy as np
from scipy import interpolate as itl
from ..elements import IVCurve
import copy

def interpolate_curve(curve: IVCurve, final_num_points: int):
    """
    Effectively increase resolution by curve interpolation
    :param curve: list or tuple of two arrays with voltages and currents
    :param final_num_points: Number points in final interpolated curve
    :return: interpolated curve in format same to the curve
    """
    curve_arr = np.array(
        (curve.voltages[1:], curve.currents[1:]), dtype=np.float32
    )

    curve_len = curve_arr.shape[1]
    raw_t = np.linspace(0, curve_len - 1, curve_len, dtype=np.float32)

    interp_function_0 = itl.interp1d(raw_t, curve_arr[0], kind="cubic")
    interp_function_1 = itl.interp1d(raw_t, curve_arr[1], kind="cubic")
    interpolated_t = np.linspace(0, curve_len - 1, final_num_points, dtype=np.float32)
    interp0 = interp_function_0(interpolated_t)
    interp1 = interp_function_1(interpolated_t)

    new_curve = copy.deepcopy(curve)
    new_curve.voltages = interp0.tolist()
    new_curve.currents = interp1.tolist()

    return new_curve


def smooth_curve(curve: IVCurve, kernel_size: int) -> IVCurve:
    """
    Remove noise by averaging
    :param curve: list or tuple of two arrays with voltages and currents
    :param kernel_size: size of averaging kernel. Should be odd.
    :return: averaged curve in format same to the curve
    """

    if kernel_size % 2 == 0:
        raise ValueError("kernel_size should be odd")

    kernel = np.ones(kernel_size) / kernel_size

    smoothed_curve = []
    lines = [curve.voltages, curve.currents]
    for line in lines:
        line = np.array(line)
        line = np.concatenate((line[-(kernel_size - 1) // 2:], line, line[:(kernel_size - 1) // 2]))
        line = np.convolve(line, kernel, mode="valid")
        smoothed_curve.append(line)

    curve.voltages = smoothed_curve[0].tolist()
    curve.currents = smoothed_curve[1].tolist()

    return curve
