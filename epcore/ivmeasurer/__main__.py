import argparse
import matplotlib
matplotlib.use("TkAgg")
from epcore.ivmeasurer import IVMeasurerIVM10, IVMeasurerVirtual
from epcore.ivmeasurer.safe_opener import BadConfig, BadFirmwareVersion
from epcore.ivmeasurer.utils import plot_curve


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("port", type=str,
                        help="Real IVM measurer COM port. Format: com:\\\\.\\COMx or /dev/ttyACM0.\n"
                             "Make sure there is 'config.ini' file in current working directory!")
    args = parser.parse_args()

    if args.port == "virtual":
        measurer = IVMeasurerVirtual()
    else:
        try:
            measurer = IVMeasurerIVM10(args.port, config="config.ini")
        except (BadConfig, BadFirmwareVersion) as exc:
            raise type(exc)("Something wrong with config file! Check example: 'epcore/ivmeasurer/config.ini'.")

    info = measurer.get_identity_information()
    print("Device info:", info)
    settings = measurer.get_settings()
    measurer.set_settings(settings)
    print("Settings:", settings)

    calibration_result = measurer.calibrate()
    print("Calibration result:", calibration_result)

    if isinstance(measurer, IVMeasurerIVM10):
        print("Get IV curve from device")
        ivc = measurer.measure_iv_curve()
        plot_curve(ivc)
    elif isinstance(measurer, IVMeasurerVirtual):
        print("Test virtual resistor")
        ivc = measurer.measure_iv_curve()
        plot_curve(ivc)

        print("Test virtual capacitor")
        settings = measurer.get_settings()
        settings.probe_signal_frequency = 1000
        settings.sampling_rate = 100000
        measurer.model = "capacitor"
        measurer.nominal = 0.000001
        print("Start measurement with low frequency...")
        ivc = measurer.measure_iv_curve()
        print("Measurement finished")
        plot_curve(ivc)
