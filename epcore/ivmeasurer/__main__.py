import logging
import argparse
from .virtual import IVMeasurerVirtual
from .measurerivm import IVMeasurerIVM10
from .measurerivm02 import IVMeasurerIVM02
from .utils import plot_curve

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)-8s %(message)s")

    logging.debug("IVMeasurer example")

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", action="store", dest="port",
                        help="Real IVM measurer COM port. Format: com:\\\\.\\COMx or /dev/ttyACM0")
    args = parser.parse_args()

    if args.port is not None:
        m = IVMeasurerIVM02(args.port, config="config.ini")
    else:
        m = IVMeasurerVirtual()

    info = m.get_identity_information()
    logging.debug("Device info: " + str(info))

    s = m.get_settings()
    m.set_settings(s)
    logging.debug("Settings: " + str(s))

    if isinstance(m, IVMeasurerIVM02):
        logging.debug("Get IV curve from device")
        ivc = m.measure_iv_curve()
        plot_curve(ivc)

    if isinstance(m, IVMeasurerVirtual):
        logging.debug("Test virtual resistor")
        ivc = m.measure_iv_curve()
        plot_curve(ivc)

        logging.debug("Test virtual capacitor")
        s = m.get_settings()
        s.probe_signal_frequency = 1  # 1 Hz
        s.sampling_rate = 100         # We want single period with 100 points
        m.model = "capacitor"
        m.nominal = 0.000001
        logging.debug("Start measurement with low frequency...")
        ivc = m.measure_iv_curve()
        logging.debug("Measurement finished")
        plot_curve(ivc)
