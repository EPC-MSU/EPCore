import logging
import numpy as np
# from .measurementplan import MeasurementPlan  # See comments below
from .ivc_comparator import IVCComparator
from .measurementsystem import MeasurementSystem
from ..elements import IVCurve
from ..ivmeasurer import IVMeasurerVirtual
from ..ivmeasurer.utils import plot_curves

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Measurement manager example")

    m1 = IVMeasurerVirtual()
    m2 = IVMeasurerVirtual()
    m2.model = "capacitor"
    m2.nominal = 0.000001

    ms = MeasurementSystem([m1, m2])
    curves = ms.measure_iv_curves()
    plot_curves(curves)

    # Seems like following commented function was removed
    # curves = ms.get_processed_curves(3)
    # plot_curves(curves)

    # This example needs MeasurementPlan arguments
    # mp = MeasurementPlan()

    logging.debug("Comparator example")
    VOLTAGE_AMPL = 12.
    R_CS = 475.
    CURRENT_AMPL = (VOLTAGE_AMPL / R_CS * 1000)

    t = np.linspace(0, 1010, 1010)
    ivc1 = IVCurve(voltages=0.88 * VOLTAGE_AMPL * np.sin(2 * np.pi * t),
                   currents=0.93 * CURRENT_AMPL * np.sin(2 * np.pi * t))
    ivc2 = IVCurve(voltages=1.45 * VOLTAGE_AMPL * np.sin(2 * np.pi * t),
                   currents=0.57 * CURRENT_AMPL * np.sin(2 * np.pi * t))
    ivc0 = IVCurve(voltages=VOLTAGE_AMPL * np.sin(2 * np.pi * t),
                   currents=CURRENT_AMPL * np.sin(2 * np.pi * t))

    comp = IVCComparator()
    comp.set_min_ivc(0., 0.)
    score1 = comp.compare_ivc(ivc1, ivc0)
    logging.debug("     Close curves: %s", score1)
    score2 = comp.compare_ivc(ivc2, ivc0)
    logging.debug(" Different curves: %s", score2)
