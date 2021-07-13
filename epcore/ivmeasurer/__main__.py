import logging
import argparse
from .safe_opener import BadFirmwareVersion, BadConfig
from .virtual import IVMeasurerVirtual
from .measurerivm import IVMeasurerIVM10
from .measurerivm02 import IVMeasurerIVM02
from .utils import plot_curve

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)-8s %(message)s")

    logging.debug("IVMeasurer example")

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", action="store", dest="port",
                        help="Real IVM measurer COM port. Format: com:\\\\.\\COMx or /dev/ttyACM0.\n"
                             "Make sure there is 'config.ini' file in current working directory!")
    parser.add_argument("-f", action="store", dest="firmware",
                        help="First two numbers of firmware version. Format: x.x")
    args = parser.parse_args()

    firmware_vs_handler = {"0.2": IVMeasurerIVM02,
                           "1.0": IVMeasurerIVM10}
    if args.port is not None:
        handler = firmware_vs_handler.get(args.firmware, None)
        if handler is None:
            supported_vers = ", ".join(firmware_vs_handler.keys())
            raise BadFirmwareVersion("Please use '-f' argument to specify one of the supported firmware versions: "
                                     "{}".format(supported_vers))
        try:
            m = handler(args.port, config="config.ini")
        except (BadConfig, BadFirmwareVersion) as e:
            raise type(e)("Something wrong with config file! Check example: 'epcore/ivmeasurer/config.ini'.")
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
