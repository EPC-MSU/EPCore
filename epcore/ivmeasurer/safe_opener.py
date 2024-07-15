"""
This module provides functionality for firmware and library compatibility check for uRPC devices.

This is a part of xigen2_utils
Don’t modify this outside xigen2_utils repository!!!
"""

import configparser
import os
from distutils.version import StrictVersion
from typing import Callable, List, Optional


class SafeOpenError(Exception):
    pass


class ConfigError(SafeOpenError):
    pass


class BadConfig(ConfigError):
    pass


class ConfigNotFound(ConfigError):
    pass


class BadControllerName(SafeOpenError):
    pass


class BadFirmwareVersion(SafeOpenError):
    pass


class GINFError(SafeOpenError):
    pass


class OpenDeviceError(SafeOpenError):
    pass


def _check_version(mask: str, version: str) -> bool:
    """
    Function checks whether the version matches the given mask. Starting from ticket #101382, the match between a
    version and a mask is determined as follows: the major and minor parts must match.
    :param mask: mask;
    :param version: version in SemVer format 'major.minor.bugfix'.
    :return: True if the version being checked is compatible with the mask.
    """

    try:
        version = _get_major_and_minor_version_parts(version)
        # For versions like 1.1.0-2.0.3
        if "-" in mask:
            version_min, version_max = mask.split("-", maxsplit=2)
            version_min = _get_major_and_minor_version_parts(version_min)
            version_max = _get_major_and_minor_version_parts(version_max)
            return version_min <= version <= version_max

        # For versions like 1.1.1
        return _get_major_and_minor_version_parts(mask) == version
    except (TypeError, ValueError):
        return False


def _get_major_and_minor_version_parts(version: str) -> StrictVersion:
    """
    :param version: version in SemVer format 'major.minor.bugfix'.
    :return: version in format 'major.minor.0'.
    """

    str_version = StrictVersion(version)
    major, minor, _ = str_version.version
    return StrictVersion(f"{major}.{minor}")


class _OpenManager:

    def __init__(self, device, config_path: str, log, force_open: bool = False) -> None:
        self._all_ok: bool = True
        self._config_path: str = config_path
        self._device = device
        self._force: bool = force_open
        self._log = log

        # These fields will be filled during the checks
        self._config = None
        self._controller_name: Optional[str] = None
        self._firmware_version: Optional[str] = None
        self._firmwares: List[str] = []
        self._library_version: Optional[str] = None

    @property
    def all_firmwares(self) -> List[str]:
        return self._firmwares

    @property
    def firmware_version(self) -> str:
        return self._firmware_version

    @property
    def library_version(self) -> str:
        return self._library_version

    @property
    def name(self) -> str:
        return self._controller_name

    @property
    def status(self) -> bool:
        return self._all_ok

    def _error(self, err: SafeOpenError, critical: bool = False) -> None:
        """
        :param err: an exception that occurred and needs to be reported in the log;
        :param critical: if True, then the device will need to be closed.
        """

        self._all_ok = False  # Something went wrong
        self._log(2, "Try to open device on port " + str(self._device.uri) + ": " + repr(err), 0)

        if self._force and not critical:
            self._log(1, "Error occurred, but device will be opened because force_open flag is set to True", 0)
        else:
            if "close_device" in dir(self._device):
                # Current naming
                self._device.close_device()
            elif "open" in dir(self._device):
                # Legacy naming
                self._device.close()
            else:
                raise RuntimeError("The device class doesn't have close_device() method")
            raise err

    def check_config(self) -> bool:
        """
        :return: True if the config file exists and can be opened.
        """

        full_path = os.path.join(os.path.dirname(__file__), self._config_path)
        if not os.path.exists(full_path):
            self._error(ConfigNotFound(full_path))
            return False

        self._config = configparser.ConfigParser()
        self._config.read(full_path, encoding="utf-8")
        return True

    def check_firmware(self) -> bool:
        """
        :return: True, if the device firmware is compatible with the epcore version.
        """

        result = False
        for opt in self._config.options(self._library_version):
            firmware_version = self.get_from_config(self._library_version, opt)
            self._firmwares.append(firmware_version)
            if _check_version(firmware_version, self._firmware_version):
                result = True

        if not result:
            self._error(BadFirmwareVersion(self._controller_name, self._library_version, self._firmware_version,
                                           self._firmwares))

        return result

    def check_ginf(self) -> bool:
        """
        :return: True, if we were able to read the controller name and firmware version.
        """

        try:
            identity = self._device.get_identity_information()
            self._controller_name = "".join([chr(c) for c in identity.controller_name]).rstrip("\x00")
            self._firmware_version = ".".join([str(x) for x in (identity.firmware_major,
                                                                identity.firmware_minor,
                                                                identity.firmware_bugfix)])
        except (ValueError, NotImplementedError, RuntimeError) as err:
            self._error(GINFError(str(err) + " occurred while reading identity information (GINF not implemented?)"))
            return False

        return True

    def check_library_version(self) -> bool:
        """
        :return: True if the device library version is supported by epcore.
        """

        self._library_version = self._device.lib_version()
        if not self._config.has_section(self._library_version):
            self._error(BadConfig("Library version " + self._library_version + " not found in config"))
            return False

        return True

    def check_name(self) -> bool:
        """
        :return: True if the device has a valid controller name.
        """

        if self._controller_name.lower() != self.get_from_config("Global", "Name").lower():
            self._error(BadControllerName(self._controller_name, self._library_version,
                                          self._firmware_version, self._firmwares))
            return False

        return True

    def checking_chain(self) -> None:
        # 1. Check open device
        self.open_device()

        # 2. Check config exists
        if not self.check_config():
            return

        # 3. Check library version in config
        if not self.check_library_version():
            return

        # 4. Check ginf
        if not self.check_ginf():
            return

        # 5. Check controller name
        if not self.check_name():
            return

        # 6. Check firmware version
        if not self.check_firmware():
            return

    def get_from_config(self, section: str, parameter: str) -> Optional[str]:
        """
        :param section:
        :param parameter:
        :return:
        """

        if not self._config.has_option(section, parameter):
            self._error(BadConfig("Section " + section + " parameter " + parameter + " not found"))
            return None

        return self._config[section][parameter]

    def open_device(self) -> None:
        try:
            if "open_device" in dir(self._device):
                # Current naming
                self._device.open_device()
            elif "open" in dir(self._device):
                # Legacy naming
                self._device.open()
            else:
                raise RuntimeError("The device class doesn't have open_device() method")
        except RuntimeError:
            self._error(OpenDeviceError(), critical=True)


def open_device_safe(uri: str, klass: type, conf: str, log: Callable, force_open: bool = False):
    """
    Function opens device safely: check versions of firmware, library and program soft.
    This function works similarly to open_device, but checks device name and protocol compatibility.
    In case of failure (and if force_open is set to False) device will be closed.
    :param uri: path to device, str (like in open_device function);
    :param klass: device handle, class;
    :param conf: path to config file, str;
    :param log: logging callback, Callable[int, str, int];
    :param force_open: device will be opened despite the errors.
    :return: device (device handle exemplar);
    :return: status (ok/not-ok)(bool);
    :return: device name (str);
    :return: library version (str);
    :return: firmware version (str);
    :return: all supported firmware versions (List[str]).
    """

    device = klass(uri, defer_open=True)
    manager = _OpenManager(device, conf, log, force_open)
    manager.checking_chain()

    return device, manager.status, manager.name, manager.library_version, manager.firmware_version, \
        manager.all_firmwares
