import numpy as np
from ..elements import IVCurve


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
