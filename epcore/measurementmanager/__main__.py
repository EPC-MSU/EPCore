import logging
from .measurementplan import MeasurementPlan
from .measurementsystem import MeasurementSystem
from ..ivmeasurer.utils import plot_curves
from ..ivmeasurer import IVMeasurerVirtual


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

    mp = MeasurementPlan()
