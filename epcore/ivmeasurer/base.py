import logging
import time
from dataclasses import dataclass

from ..elements import MeasurementSettings, IVCurve


@dataclass
class IVMeasurerIdentityInformation:
    """
    Class for hardware identity information
    in unified format
    """
    manufacturer: str
    device_class: str
    device_name: str
    hardware_version: tuple
    firmware_version: tuple
    name: str


class IVMeasurerBase:
    """
    Base class, which implements standard interface for
    all IVMeasurers
    """
    def __init__(self, url: str = "") -> "IVMeasurerBase":
        """
        :param url: url for device identification in computer system.
        For serial devices url will be "com:\\\\.\\COMx" (for Windows)
        or "com:///dev/tty/ttyACMx"
        """
        self.url = url
        logging.debug("IVMeasurerBase created")

    def set_settings(self, settings: MeasurementSettings):
        pass

    def get_settings(self) -> MeasurementSettings:
        return MeasurementSettings(
            sampling_rate=0,
            internal_resistance=0,
            probe_signal_frequency=0,
            max_voltage=0
        )

    def get_identity_information(self) -> IVMeasurerIdentityInformation:
        return IVMeasurerIdentityInformation()

    def trigger_measurement(self):
        """
        Trigger measurement manually.
        You don’t need this if the hardware is in continuous mode.
        """
        pass

    def measurement_is_ready(self) -> bool:
        """
        Return true if new measurement is ready
        """
        return True

    def get_last_iv_curve(self) -> IVCurve:
        """
        Return result of the last measurement.
        """
        return IVCurve()

    def measure_iv_curve(self) -> IVCurve:
        """
        Perform measurement and return result for the measurement, which was made.
        Blocking function. May take some time.
        """
        self.trigger_measurement()
        while not self.measurement_is_ready():
            time.sleep(0.05)
        return self.get_last_iv_curve()
