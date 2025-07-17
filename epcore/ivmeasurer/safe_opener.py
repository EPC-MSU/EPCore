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
        """
        :param device: device;
        :param config_path: path to config file;
        :param log: logging callback;
        :param force_open: device will be opened despite the errors.
        """

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
    def controller_name(self) -> str:
        return self._controller_name

    @property
    def firmware_version(self) -> str:
        return self._firmware_version

    @property
    def library_version(self) -> str:
        return self._library_version

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

    def _check_config(self) -> bool:
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

    def _check_controller_name(self) -> bool:
        """
        :return: True if the device has a valid controller name.
        """

        controller_name_from_config = self._get_from_config("Global", "Name")
        if controller_name_from_config is None:
            self._error(BadConfig("The configuration file does not have a 'Global' section with the 'Name' key"))
            return False

        if self._controller_name.lower() != controller_name_from_config.lower():
            self._error(BadControllerName(self._controller_name, self._library_version,
                                          self._firmware_version, controller_name_from_config))
            return False

        return True

    def _check_firmware_version(self) -> bool:
        """
        :return: True, if the device firmware is compatible with the epcore version.
        """

        result = False
        for opt in self._config.options(self._library_version):
            compatible_firmware_version = self._config[self._library_version][opt]
            self._firmwares.append(compatible_firmware_version)
            if _check_version(compatible_firmware_version, self._firmware_version):
                result = True

        if not result:
            self._error(BadFirmwareVersion(self._controller_name, self._library_version, self._firmware_version,
                                           self._firmwares))

        return result

    def _check_ginf(self) -> bool:
        """
        :return: True, if we were able to read the controller name and firmware version.
        """

        try:
            identity = self._device.get_identity_information()
            self._controller_name = "".join([chr(c) for c in identity.controller_name]).rstrip("\x00")
            self._firmware_version = ".".join([str(x) for x in (identity.firmware_major,
                                                                identity.firmware_minor,
                                                                identity.firmware_bugfix)])
            self._library_version = self._device.lib_version()
        except (ValueError, NotImplementedError, RuntimeError) as exc:
            self._error(GINFError(str(exc) + " occurred while reading identity information (GINF not implemented?)"))
            return False

        return True

    def _check_library_version(self) -> bool:
        """
        :return: True if the device library version is supported by epcore.
        """

        if not self._config.has_section(self._library_version):
            self._error(BadFirmwareVersion(self._controller_name, self._library_version, self._firmware_version, []))
            return False

        return True

    def _get_from_config(self, section: str, parameter: str) -> Optional[str]:
        """
        :param section: section name in the configuration file;
        :param parameter: option name in the configuration file.
        :return: option value from the configuration file.
        """

        if not self._config.has_option(section, parameter):
            return None

        return self._config[section][parameter]

    def _open_device(self) -> None:
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

    def check_device_for_compatibility(self) -> None:
        # 1. Check open device
        self._open_device()

        # 2. Check config exists
        if not self._check_config():
            return

        # 3. Check ginf
        if not self._check_ginf():
            return

        # 4. Check controller name
        if not self._check_controller_name():
            return

        # 5. Check library version in config
        if not self._check_library_version():
            return

        # 6. Check firmware version
        if not self._check_firmware_version():
            return


def open_device_safe(uri: str, klass: type, config_path: str, log: Callable, force_open: bool = False):
    """
    Function opens device safely: check versions of firmware, library and program soft.
    This function works similarly to open_device, but checks device name and protocol compatibility.
    In case of failure (and if force_open is set to False) device will be closed.
    :param uri: path to device, str (like in open_device function);
    :param klass: device handle, class;
    :param config_path: path to config file, str;
    :param log: logging callback, Callable[int, str, int];
    :param force_open: device will be opened despite the errors.
    :return: device (device handle exemplar);
    :return: status (ok/not-ok) (bool);
    :return: device name (str);
    :return: library version (str);
    :return: firmware version (str);
    :return: all supported firmware versions (List[str]).
    """

    device = klass(uri, defer_open=True)
    manager = _OpenManager(device, config_path, log, force_open)
    manager.check_device_for_compatibility()

    return (device, manager.status, manager.controller_name, manager.library_version, manager.firmware_version,
            manager.all_firmwares)
