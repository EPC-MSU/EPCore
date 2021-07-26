"""
File with base class which implements standard interface for all IVMeasurers.
"""

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict
from ..elements import MeasurementSettings, IVCurve


@dataclass
class IVMeasurerIdentityInformation:
    """
    Class for hardware identity information in unified format.
    """

    manufacturer: str
    device_class: str
    device_name: str
    hardware_version: tuple
    firmware_version: tuple
    name: str
    rank: int


class IVMeasurerBase(ABC):
    """
    Base class which implements standard interface for all IVMeasurers.
    """

    def __init__(self, url: str = "", name: str = ""):
        """
        :param url: url for device identification in computer system. For
        serial devices url will be "com:\\\\.\\COMx" (for Windows) or
        "com:///dev/tty/ttyACMx" (for Linux);
        :param name: friendly name (for measurement system).
        """

        self._url = url
        self._name = name
        self._cashed_curve = None
        self._freeze = False
        logging.debug("IVMeasurerBase created")

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    @name.setter
    def name(self, name: str):
        self._name = name

    @abstractmethod
    def open_device(self):
        """
        Open device. You don't need that if defer_open is False.
        """

        raise NotImplementedError()

    @abstractmethod
    def reconnect(self) -> bool:
        raise NotImplementedError()

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
        Trigger measurement manually. You don’t need this if the hardware is
        in continuous mode.
        """

        raise NotImplementedError()

    @abstractmethod
    def measurement_is_ready(self) -> bool:
        """
        Return True if new measurement is ready.
        """

        raise NotImplementedError()

    @abstractmethod
    def calibrate(self, *args):
        """
        Calibrate IVC.
        :param args: arguments.
        """

        raise NotImplementedError()

    @abstractmethod
    def get_last_iv_curve(self) -> IVCurve:
        """
        Return result of the last measurement.
        :return: last measurement.
        """

        raise NotImplementedError()

    @abstractmethod
    def get_current_value_of_parameter(self, attribute_name: str) -> Any:
        """
        Method returns current value of measurer parameter with given name.
        :return: current value of parameter.
        """

        raise NotImplementedError()

    @abstractmethod
    def set_value_to_parameter(self, attribute_name: str, value: Any):
        """
        Method sets value to attribute of measurer with given name.
        :param attribute_name: name of attribute;
        :param value: value for attribute.
        """

        raise NotImplementedError()

    def get_last_cached_iv_curve(self) -> IVCurve:
        """
        Return result of the last measurement. Even if the result is not yet
        ready, the previous result will be returned.
        :return: last measurement.
        """

        if self.measurement_is_ready():
            return self.get_last_iv_curve()
        if self._cashed_curve is None:
            raise ValueError("Cache is empty")
        return self._cashed_curve

    def freeze(self):
        self._freeze = True

    def unfreeze(self):
        self._freeze = False

    def is_freezed(self) -> bool:
        return self._freeze

    def measure_iv_curve(self) -> IVCurve:
        """
        Perform measurement and return result for the measurement, which was
        made. Blocking function. May take some time.
        """

        if self._freeze:
            return self.get_last_cached_iv_curve()
        self.trigger_measurement()
        while not self.measurement_is_ready():
            time.sleep(0.05)
        return self.get_last_iv_curve()

    def get_all_settings(self) -> Dict:
        """
        Method returns all settings for measurer.
        :return: dictionary with all settings.
        """

        identity_info = self.get_identity_information()
        device_class = identity_info.device_class
        dir_name = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(dir_name, f"{device_class} settings.json")
        filename = filename.replace(" ", "_")
        if not os.path.exists(filename):
            return {}
        with open(filename, "r", encoding="utf-8") as file:
            settings = json.load(file)
        return settings


def cache_curve(func: Callable) -> Callable:
    def wrap(self, *args, **kwargs):
        curve = func(self, *args, **kwargs)
        self._cashed_curve = curve
        return curve
    return wrap
