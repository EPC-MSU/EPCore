import logging
import argparse
from .virtual import IVMeasurerVirtual
from .measurerivm import IVMeasurerIVM10
from .utils import plot_curve

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    logging.debug("IVMeasurere example")

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", action="store", dest="port",
                        help="Real IVM measurer COM port. Fotmat: com:\\\\.\\COMx or /dev/ttyACM0")
    args = parser.parse_args()

    if args.port is not None:
        m = IVMeasurerIVM10(args.port)
    else:
        m = IVMeasurerVirtual()

    info = m.get_identity_information()
    logging.debug("Device info: " + str(info))

    s = m.get_settings()
    m.set_settings(s)
    logging.debug("Settings: " + str(s))

    if isinstance(m, IVMeasurerIVM10):
        logging.debug("Get IV curve from device")
        ivc = m.measure_iv_curve()
        plot_curve(ivc)

    if isinstance(m, IVMeasurerVirtual):
        logging.debug("Test virtual resistor")
        ivc = m.measure_iv_curve()
        plot_curve(ivc)

        logging.debug("Test virtual capacitor")
        m.model = "capacitor"
        m.nominal = 0.000001
        ivc = m.measure_iv_curve()
        plot_curve(ivc)
