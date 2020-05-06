import logging
from .base import IVMeasurerBase
from .virtual import IVMeasurerVirtual
from .utils import plot_curve

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    logging.debug("IVMeasurere example")
    
    m = IVMeasurerVirtual()
    info = m.get_identity_information()
    print(info)
    s = m.get_settings()
    m.set_settings(s)
    print(s)
    ivc = m.measure_iv_curve()
    plot_curve(ivc)
