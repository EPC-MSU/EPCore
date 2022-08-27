import logging
from typing import List
import matplotlib.pyplot as plt
import numpy as np
from epcore.elements import IVCurve


def plot_curve(iv_curve: IVCurve):
    """
    Function draws given IV-curve.
    :param iv_curve: IV-curve to draw.
    """

    plot_curves([iv_curve])


def plot_curves(iv_curves: List[IVCurve]):
    """
    Function draws IV-curves from given list.
    :param iv_curves: list of IV-curves.
    """

    logging.disable(logging.WARNING)  # Matplotlib has useless output
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.title("Сигналы")
    for curve_index, iv_curve in enumerate(iv_curves):
        plt.plot(iv_curve.voltages, linestyle="None", marker="o", label="Напряжение [{}], В".format(curve_index))
        plt.plot(np.array(iv_curve.currents) * 1000, linestyle="None", marker="o",
                 label="Ток [{}], мА".format(curve_index))
    plt.legend()
    plt.grid()
    plt.subplot(1, 2, 2)
    plt.title("ВАХ")
    for curve_index, iv_curve in enumerate(iv_curves):
        plt.plot(iv_curve.voltages, np.array(iv_curve.currents) * 1000, linestyle="None", marker="o",
                 label="ВАХ [{}]".format(curve_index))
    plt.legend()
    plt.grid()
    plt.xlabel("Напряжение, В")
    plt.ylabel("Ток, мА")
    plt.show()
    logging.disable(0)  # Enable logging back
