import argparse
import logging
from .measurerasa import IVMeasurerASA
from .measurerivm import IVMeasurerIVM10
from .utils import plot_curve
from .virtual import IVMeasurerVirtual

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)-8s %(message)s")
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
    logging.debug("Device info: %s", str(info))
    s = m.get_settings()
    m.set_settings(s)
    logging.debug("Settings: %s", str(s))
    if isinstance(m, IVMeasurerIVM10):
        logging.debug("Get IV curve from device")
        ivc = m.measure_iv_curve()
        plot_curve(ivc)
    elif isinstance(m, IVMeasurerVirtual):
        logging.debug("Test virtual resistor")
        ivc = m.measure_iv_curve()
        plot_curve(ivc)

        logging.debug("Test virtual capacitor")
        s = m.get_settings()
        s.probe_signal_frequency = 1000
        s.sampling_rate = 100000
        m.model = "capacitor"
        m.nominal = 0.000001
        logging.debug("Start measurement with low frequency...")
        ivc = m.measure_iv_curve()
        logging.debug("Measurement finished")
        plot_curve(ivc)

    # Work with IVMeasurerASA
    measurer = IVMeasurerASA("xmlrpc:172.16.3.213", "asa_measurer", True)
    measurer.open_device()
    settings = measurer.get_settings()

    logging.debug("Test virtual ASA resistor")
    measurer.set_value_to_parameter("model_type", "resistor")
    measurer.set_value_to_parameter("model_nominal", 100)
    measurer.set_value_to_parameter("mode", "manual")
    settings.probe_signal_frequency = 100
    settings.sampling_rate = 10000
    settings.max_voltage = 5
    settings.internal_resistance = 1000 * 5 / 5
    measurer.set_settings(settings)
    new_settings = measurer.get_settings()
    ivc = measurer.measure_iv_curve()
    plot_curve(ivc)

    logging.debug("Test virtual ASA capacitor")
    measurer.set_value_to_parameter("model_type", "capacitor")
    measurer.set_value_to_parameter("model_nominal", 0.000001)
    settings.probe_signal_frequency = 1500
    settings.sampling_rate = 150000
    settings.max_voltage = 10
    settings.internal_resistance = 1000 * 10 / 5
    measurer.set_settings(settings)
    new_settings = measurer.get_settings()
    ivc = measurer.measure_iv_curve()
    plot_curve(ivc)
