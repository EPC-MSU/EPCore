"""
File with base class which implements standard interface for all IVMeasurers.
"""

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional
from ..elements import IVCurve, MeasurementSettings


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

    def __init__(self, url: str = "", name: str = "") -> None:
        """
        :param url: url for device identification in computer system.
        For serial devices url will be "com:\\\\.\\COMx" (for Windows) or "com:///dev/ttyACMx" (for Linux);
        :param name: friendly name (for measurement system).
        """

        self._cashed_curve: IVCurve = None
        self._freeze: bool = False
        self._name: str = name
        self._url: str = url
        logging.debug("IVMeasurerBase created")

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        self._name = name

    @property
    def url(self) -> str:
        return self._url

    @url.setter
    def url(self, url: str) -> None:
        self._url = url

    @abstractmethod
    def calibrate(self, *args) -> Optional[int]:
        """
        Calibrates device.
        :param args: arguments.
        :return: calibration result code.
        """

        raise NotImplementedError()

    def freeze(self) -> None:
        self._freeze = True

    def get_all_settings(self) -> Dict[str, Any]:
        """
        :return: dictionary with all settings for measurer device.
        """

        identity_info = self.get_identity_information()
        device_class = identity_info.device_class
        dir_name = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(dir_name, f"{device_class} settings.json".replace(" ", "_"))
        if not os.path.exists(filename):
            return {}

        with open(filename, "r", encoding="utf-8") as file:
            settings = json.load(file)
        return settings

    def get_current_value_of_parameter(self, attribute_name: str) -> Any:
        """
        :return: current value of measurer device parameter with given name.
        """

        return getattr(self, attribute_name, None)

    @abstractmethod
    def get_identity_information(self) -> IVMeasurerIdentityInformation:
        """
        :return: main identity information about device.
        """

        raise NotImplementedError()

    def get_last_cached_iv_curve(self) -> IVCurve:
        """
        :return: result of the last measurement. Even if the result is not yet ready, the previous result will be
        returned.
        """

        if self.measurement_is_ready():
            return self.get_last_iv_curve()
        if self._cashed_curve is None:
            raise ValueError("Cache is empty")
        return self._cashed_curve

    @abstractmethod
    def get_last_iv_curve(self) -> IVCurve:
        """
        :return: last measurement.
        """

        raise NotImplementedError()

    @abstractmethod
    def get_settings(self) -> MeasurementSettings:
        """
        :return: measurement settings set on the device.
        """

        raise NotImplementedError()

    def is_freezed(self) -> bool:
        """
        :return: True if measurements are frozen.
        """

        return self._freeze

    def measure_iv_curve(self) -> IVCurve:
        """
        Performs measurement. Blocking function. May take some time.
        :return: result for measurement.
        """

        if self._freeze:
            return self.get_last_cached_iv_curve()
        self.trigger_measurement()
        while not self.measurement_is_ready():
            time.sleep(0.05)
        return self.get_last_iv_curve()

    @abstractmethod
    def measurement_is_ready(self) -> bool:
        """
        :return: True if new measurement is ready.
        """

        raise NotImplementedError()

    @abstractmethod
    def open_device(self):
        """
        Opens device. You don't need that if defer_open is False.
        """

        raise NotImplementedError()

    @abstractmethod
    def reconnect(self) -> bool:
        """
        :return: True if the reconnect was successful.
        """

        raise NotImplementedError()

    @abstractmethod
    def set_settings(self, settings: MeasurementSettings) -> None:
        """
        :param settings: measurement settings to be set on device.
        """

        raise NotImplementedError()

    def set_value_to_parameter(self, attribute_name: str, value: Any) -> None:
        """
        Sets value to parameter of measurer device with given name.
        :param attribute_name: name of attribute;
        :param value: value for attribute.
        """

        if attribute_name in self.__dict__:
            setattr(self, attribute_name, value)

    @abstractmethod
    def trigger_measurement(self) -> None:
        """
        Triggers measurement manually. You don’t need this if the hardware is in continuous mode.
        """

        raise NotImplementedError()

    def unfreeze(self) -> None:
        self._freeze = False


def cache_curve(func: Callable) -> Callable:
    def wrap(self, *args, **kwargs):
        curve = func(self, *args, **kwargs)
        self._cashed_curve = curve
        return curve
    return wrap


def close_on_error(func: Callable[..., Any]):
    """
    Due to the nature of the uRPC library uRPC device must be immediately closed after first error.
    :param func: IVMeasurerIVM method.
    :return: IVMeasurerIVM decorated method.
    """

    def handle(self, *args, **kwargs) -> Any:
        try:
            return func(self, *args, **kwargs)
        except (RuntimeError, OSError) as exc:
            self.close_device()
            raise exc
    return handle
