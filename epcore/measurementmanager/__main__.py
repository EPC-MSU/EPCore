import logging
import numpy as np
from .ivc_comparator import IVCComparator
from .measurementplan import MeasurementPlan
from .measurementsystem import MeasurementSystem
from ..elements import Board, Element, IVCurve, Pin
from ..ivmeasurer import IVMeasurerVirtual
from ..ivmeasurer.utils import plot_curves


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Measurement system example")
    measurer_1 = IVMeasurerVirtual()
    measurer_2 = IVMeasurerVirtual()
    measurer_2.model = "capacitor"
    measurer_2.nominal = 0.000001
    measurement_system = MeasurementSystem([measurer_1, measurer_2])
    curves = measurement_system.measure_iv_curves()
    plot_curves(curves)

    logging.debug("Measurement plan example")
    board = Board(elements=[Element(pins=[Pin(x=0, y=0, measurements=[])])])
    measurement_plan = MeasurementPlan(board, measurer_1)
    measurement_plan.save_last_measurement_as_reference()
    logging.debug("Current pin index: %s", measurement_plan.get_current_index())

    logging.debug("Comparator example")
    VOLTAGE_AMPL = 12.
    R_CS = 475.
    CURRENT_AMPL = (VOLTAGE_AMPL / R_CS * 1000)
    times = np.linspace(0, 1010, 1010)
    iv_curve_0 = IVCurve(voltages=VOLTAGE_AMPL * np.sin(2 * np.pi * times),
                         currents=CURRENT_AMPL * np.sin(2 * np.pi * times))
    iv_curve_1 = IVCurve(voltages=0.88 * VOLTAGE_AMPL * np.sin(2 * np.pi * times),
                         currents=0.93 * CURRENT_AMPL * np.sin(2 * np.pi * times))
    iv_curve_2 = IVCurve(voltages=1.45 * VOLTAGE_AMPL * np.sin(2 * np.pi * times),
                         currents=0.57 * CURRENT_AMPL * np.sin(2 * np.pi * times))
    plot_curves([iv_curve_0, iv_curve_1, iv_curve_2])
    comparator = IVCComparator()
    comparator.set_min_ivc(0.03 * VOLTAGE_AMPL, 0.03 * CURRENT_AMPL)
    score1 = comparator.compare_ivc(iv_curve_1, iv_curve_0)
    logging.debug("Score for close curves: %s", score1)
    score2 = comparator.compare_ivc(iv_curve_2, iv_curve_0)
    logging.debug("Score for different curves: %s", score2)
