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
