import logging
from .base import IVMeasurerBase

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    logging.debug("IVMeasurere example")
    
    m = IVMeasurerBase()
    info = m.get_identity_information()
    s = m.get_settings()
    m.set_settings(s)
    ivc = m.measure_iv_curve()
