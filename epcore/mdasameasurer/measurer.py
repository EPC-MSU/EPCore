"""
File with class for Meridian measurer.
"""

import time
from enum import Enum
from threading import Thread, Lock
from typing import Tuple
from .device_handler import MdasaDeviceHandler
from .elements import MeasurementSettings


def _parse_address(full_address: str) -> Tuple[str, str]:
    """
    Function parses full device address into its component parts.
    :param full_address: full device address.
    :return: IP address and port of device.
    """

    address_parts = full_address.split(":")
    port = None
    if len(address_parts) == 3:
        protocol, ip_address, port = address_parts
    else:
        protocol, ip_address = address_parts
    if protocol != "xmlrpc":
        raise ValueError("Wrong protocol for Mdasa measurer")
    return ip_address, port


class IvcStatus(Enum):
    SUCCESS = 0
    FAILED = 1


class MdasaMeasurer:
    """
    Class for Meridian measurer.
    """

    def __init__(self, address: str, name: str = "", defer_open: bool = False):
        """
        :param address: address of server in format "xmlrpc:xxx.xxx.xxx.xxx:x";
        :param name: friendly name (for measurement system);
        :param defer_open: if True there will not be connection to server
        during initialization.
        """

        self._host, self._port = _parse_address(address)
        self._name = name
        self._device_handler = MdasaDeviceHandler()
        self._lock = Lock()
        self._need_run: bool = False
        self._bg_thread = None
        self.connection_status: bool = False
        if not defer_open:
            self.start()

    def _run(self) -> None:
        is_virtual = isinstance(self._device_handler, MdasaDeviceHandler)
        with self._lock:
            while True:
                if not self._need_run:
                    break
                if (self._device_handler.server is not None and
                        self._device_handler.connection_status):
                    while self._device_handler.get_status_operation() == 1:
                        time.sleep(0.2)
                    try:
                        measurement = self._device_handler.measure()
                    except Exception as exc:
                        self._device_handler.logger.error(
                            "Measure failed. Something went wrong: %s", exc)
                    try:
                        self._device_handler.get_status_button_probes()
                    except Exception as exc:
                        self._device_handler.logger.error(
                            "GetStatusButton for probes failed. Something went wrong: %s",
                            exc)
                    measurement_control = (self._device_handler.save_settings,
                                           self._device_handler.save_result)
                    temp = self._device_handler.temp_probe()
                    self.measure_ready.emit(measurement)
                    self.measure_control_ready.emit(measurement_control)
                    self.temp_probes.emit(temp)
                self.status_connect.emit(self._device_handler.connection_status)
                self.calibration_status.emit(self._device_handler.calibration_status)
                self._device_handler.calibration_status = ("", "")
            if is_virtual:
                time.sleep(0.2)
        self.ivc_stopped.emit(IvcStatus.SUCCESS)

    def calibrate_value(self, value: str):
        with self._lock:
            if value:
                self._device_handler.calibrate(value)

    def get_settings(self) -> MeasurementSettings:
        """
        Method returns measurement settings in device.
        :return: measurement settings.
        """

        return self._device_handler.get_settings()

    def make_measurement(self, measure: bool):
        with self._lock:
            if measure:
                self._device_handler.make_measurement()

    @property
    def name(self):
        return self._name

    def set_freezed_state(self, freeze: bool):
        with self._lock:
            if freeze is True:
                self._device_handler.freeze_ivc()
            else:
                self._device_handler.save_settings = None
                self._device_handler.save_result = None

    def set_host(self):
        """
        Method sets address of device and try to connect to device.
        """

        with self._lock:
            self._device_handler.set_server_host(self._host, self._port)
            try:
                self._device_handler.load_and_set_coefficients()
                # self._device_handler.set_settings()
            except Exception as exc:
                self.connection_status = False
                raise ConnectionError(
                    "There are problems with connection to server") from exc
            if self._device_handler.connection_status:
                try:
                    while self._device_handler.get_status_operation() > 0:
                        time.sleep(0.2)
                    if self._device_handler.get_status_operation() < 0:
                        raise RuntimeError
                    self._device_handler.make_measurement()
                except Exception as exc:
                    self.connection_status = False
                    raise ConnectionError(
                        "There are problem with connection to server") from exc
            self.connection_status = True

    def set_settings(self, **kwargs):
        """
        Method sets settings to device.
        :param kwargs: new settings.
        """

        with self._lock:
            if kwargs is not None:
                self._device_handler.set_settings(**kwargs)

    def start(self):
        """
        Method starts the device.
        """

        need_start = False
        with self._lock:
            if not self._need_run:
                need_start = True
                self._need_run = True
                self.set_host()
                self._bg_thread = Thread(target=self._run)
        if need_start:
            self._bg_thread.start()

    def stop(self):
        """
        Method stops the operation of device.
        """

        need_stop = False
        with self._lock:
            if self._need_run:
                need_stop = True
                self._need_run = False
        if need_stop:
            self._bg_thread.join()
