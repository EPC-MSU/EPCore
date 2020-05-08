import logging
from .base import IVMeasurerBase
from .virtual import IVMeasurerVirtual
from .utils import plot_curve

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    logging.debug("IVMeasurere example")

    m = IVMeasurerVirtual()
    info = m.get_identity_information()
    logging.debug("Device info: " + str(info))

    s = m.get_settings()
    m.set_settings(s)
    logging.debug("Settings: " + str(s))
    
    logging.debug("Test virtual resistor")
    ivc = m.measure_iv_curve()
    plot_curve(ivc)

    logging.debug("Test virtual capacitor")
    m.model = "capacitor"
    m.nominal = 0.000001
    ivc = m.measure_iv_curve()
    plot_curve(ivc)
