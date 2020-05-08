import logging
import time
from dataclasses import dataclass
from abc import ABC, abstractmethod

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


class IVMeasurerBase(ABC):
    """
    Base class, which implements standard interface for
    all IVMeasurers
    """
    def __init__(self, url: str = ""):
        """
        :param url: url for device identification in computer system.
        For serial devices url will be "com:\\\\.\\COMx" (for Windows)
        or "com:///dev/tty/ttyACMx"
        """
        self.url = url
        logging.debug("IVMeasurerBase created")

    @abstractmethod
    def set_settings(self, settings: MeasurementSettings):
        raise NotImplementedError()

    @abstractmethod
    def get_settings(self) -> MeasurementSettings:
        raise NotImplementedError()

    @abstractmethod
    def get_identity_information(self) -> IVMeasurerIdentityInformation:
        raise NotImplementedError()

    @abstractmethod
    def trigger_measurement(self):
        """
        Trigger measurement manually.
        You don’t need this if the hardware is in continuous mode.
        """
        raise NotImplementedError()

    @abstractmethod
    def measurement_is_ready(self) -> bool:
        """
        Return true if new measurement is ready
        """
        raise NotImplementedError()

    @abstractmethod
    def get_last_iv_curve(self) -> IVCurve:
        """
        Return result of the last measurement.
        """
        raise NotImplementedError()

    def measure_iv_curve(self) -> IVCurve:
        """
        Perform measurement and return result for the measurement, which was made.
        Blocking function. May take some time.
        """
        self.trigger_measurement()
        while not self.measurement_is_ready():
            time.sleep(0.05)
        return self.get_last_iv_curve()
