import matplotlib.pyplot as plt
import numpy as np
from ..elements import IVCurve

def plot_curve(ivc: IVCurve): 
    plt.figure(figsize=(12, 5))

    plt.subplot(1, 2, 1)
    plt.title("Сигналы")
    plt.plot(ivc.voltages, linestyle="None", marker="o", label="Напряжение, В")
    plt.plot(np.array(ivc.currents) * 1000, linestyle="None", marker="o", label="Ток, мА")

    plt.subplot(1, 2, 2)
    plt.title("ВАХ")
    plt.plot(ivc.voltages, 
             np.array(ivc.currents)*1000, 
             linestyle="None", marker="o", label="Напряжение")
    plt.xlabel("Напряжение, В")
    plt.ylabel("Ток, мА")

    plt.show()
