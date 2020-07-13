import matplotlib.pyplot as plt
import numpy as np
import logging
from ..elements import IVCurve
from typing import List


def plot_curves(ivcs: List[IVCurve]):
    logging.disable(logging.WARNING)  # Matplotlib has useless output

    plt.figure(figsize=(12, 5))

    plt.subplot(1, 2, 1)
    plt.title("Сигналы")
    for i, ivc in enumerate(ivcs):
        plt.plot(ivc.voltages, linestyle="None", marker="o",
                 label="Напряжение [{}], В".format(i))
        plt.plot(np.array(ivc.currents) * 1000, linestyle="None", marker="o",
                 label="Ток [{}], мА".format(i))
    plt.legend()

    plt.subplot(1, 2, 2)
    plt.title("ВАХ")
    for i, ivc in enumerate(ivcs):
        plt.plot(ivc.voltages,
                 np.array(ivc.currents)*1000,
                 linestyle="None", marker="o",
                 label="ВАХ [{}]".format(i))
    plt.legend()
    plt.xlabel("Напряжение, В")
    plt.ylabel("Ток, мА")

    plt.show()

    logging.disable(0)  # Enable logging back


def plot_curve(ivc: IVCurve):
    plot_curves([ivc])


def smooth_curve(self, curve: IVCurve, kernel_size: int) -> IVCurve:
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
