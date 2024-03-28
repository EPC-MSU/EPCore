import argparse
import logging
import sys
from epcore.ivmeasurer import IVMeasurerASA, IVMeasurerIVM02, IVMeasurerIVM10, IVMeasurerVirtual
from epcore.ivmeasurer.safe_opener import BadConfig, BadFirmwareVersion
from epcore.ivmeasurer.utils import plot_curve


def work_with_asa_device(ip_address: str) -> None:
    """
    Function to work with ASA device.
    :param ip_address: IP address of ASA device server.
    """

    measurer_asa = IVMeasurerASA(ip_address, "asa_measurer", True)
    measurer_asa.open_device()
    settings = measurer_asa.get_settings()

    logging.debug("Test virtual ASA resistor")
    measurer_asa.set_value_to_parameter("model_type", "resistor")
    measurer_asa.set_value_to_parameter("model_nominal", 100)
    measurer_asa.set_value_to_parameter("mode", "manual")
    settings.probe_signal_frequency = 100
    settings.sampling_rate = 10000
    settings.max_voltage = 5
    settings.internal_resistance = 1000 * 5 / 5
    measurer_asa.set_settings(settings)
    plot_curve(measurer_asa.measure_iv_curve())

    logging.debug("Test virtual ASA capacitor")
    measurer_asa.set_value_to_parameter("model_type", "capacitor")
    measurer_asa.set_value_to_parameter("model_nominal", 0.000001)
    settings.probe_signal_frequency = 1500
    settings.sampling_rate = 150000
    settings.max_voltage = 10
    settings.internal_resistance = 1000 * 10 / 5
    measurer_asa.set_settings(settings)
    plot_curve(measurer_asa.measure_iv_curve())


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
        if "xmlrpc" in args.port:
            work_with_asa_device(args.port)
            sys.exit(0)

        handler = firmware_vs_handler.get(args.firmware, None)
        if handler is None:
            supported_vers = ", ".join(firmware_vs_handler.keys())
            raise BadFirmwareVersion("Please use '-f' argument to specify one of the supported firmware versions: "
                                     "{}".format(supported_vers))

        try:
            measurer = handler(args.port, config="config.ini")
        except (BadConfig, BadFirmwareVersion) as exc:
            raise type(exc)("Something wrong with config file! Check example: 'epcore/ivmeasurer/config.ini'.")
    else:
        measurer = IVMeasurerVirtual()

    info = measurer.get_identity_information()
    logging.debug("Device info: %s", str(info))
    settings = measurer.get_settings()
    measurer.set_settings(settings)
    logging.debug("Settings: %s", str(settings))

    calibration_result = measurer.calibrate()
    logging.debug("Calibration result: %s", calibration_result)

    if isinstance(measurer, (IVMeasurerIVM02, IVMeasurerIVM10)):
        logging.debug("Get IV curve from device")
        ivc = measurer.measure_iv_curve()
        plot_curve(ivc)
    elif isinstance(measurer, IVMeasurerVirtual):
        logging.debug("Test virtual resistor")
        ivc = measurer.measure_iv_curve()
        plot_curve(ivc)

        logging.debug("Test virtual capacitor")
        settings = measurer.get_settings()
        settings.probe_signal_frequency = 1000
        settings.sampling_rate = 100000
        measurer.model = "capacitor"
        measurer.nominal = 0.000001
        logging.debug("Start measurement with low frequency...")
        ivc = measurer.measure_iv_curve()
        logging.debug("Measurement finished")
        plot_curve(ivc)
