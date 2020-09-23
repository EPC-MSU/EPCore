import os
import configparser
from distutils.version import StrictVersion


class SafeOpenError(Exception):
    pass


class ConfigError(SafeOpenError):
    pass


class ConfigNotFound(ConfigError):
    pass


class BadConfig(ConfigError):
    pass


class OpenDeviceError(SafeOpenError):
    pass


class GINFError(SafeOpenError):
    pass


class BadControllerName(SafeOpenError):
    pass


class BadFirmwareVersion(SafeOpenError):
    pass


def _check_version(mask: str, version: str) -> bool:
    try:
        # For versions like 1.1.0-2.0.3
        if "-" in mask:
            vmin, vmax = mask.split("-", maxsplit=2)
            return StrictVersion(vmin) <= StrictVersion(version) <= StrictVersion(vmax)

        # For versions like 1.1.1
        return StrictVersion(mask) == StrictVersion(version)
    except (TypeError, ValueError):
        return False


class _OpenManager:
    def __init__(self, device, config_path: str, log, force_open: bool = False):
        self._force = force_open
        self._log = log
        self._device = device
        self._config_path = config_path

        self._all_ok = True

        # These fields will be filled during the checks
        self._config = None
        self._controller_name = None
        self._firmware_version = None
        self._firmwares = []
        self._library_version = None

    def error(self, err: SafeOpenError, critical: bool = False):
        self._all_ok = False  # Something went wrong

        self._log(2, "Try to open device on port " + str(self._device.uri) + ": " + repr(err), 0)

        if self._force and not critical:
            self._log(1, "Error occurred, but device will be opened because force_open flag is set to True", 0)
        else:
            self._device.close()
            raise err

    def get_from_config(self, section: str, parameter: str):
        if not self._config.has_option(section, parameter):
            self.error(BadConfig("Section " + section + " parameter " + parameter + " not found"))
            return None
        return self._config[section][parameter]  # type: str

    def check_config(self) -> bool:
        full_path = os.path.join(os.path.dirname(__file__), self._config_path)
        if not os.path.exists(full_path):
            self.error(ConfigNotFound(full_path))
            return False

        self._config = configparser.ConfigParser()
        self._config.read(full_path, encoding="utf-8")

        return True

    def open_device(self):
        try:
            self._device.open()
        except RuntimeError:
            self.error(OpenDeviceError(), critical=True)

    def check_ginf(self) -> bool:
        try:
            identity = self._device.get_identity_information()
            self._controller_name = "".join([chr(c) for c in identity.controller_name]).rstrip("\x00")
            self._firmware_version = ".".join([str(x) for x in (identity.firmware_major,
                                                                identity.firmware_minor,
                                                                identity.firmware_bugfix)])
        except (ValueError, NotImplementedError, RuntimeError) as err:
            self.error(GINFError(str(err) + " occurred while reading identity information (GINF not implemented?)"))
            return False

        return True

    def check_library_version(self) -> bool:
        self._library_version = self._device.lib_version()
        if not self._config.has_section(self._library_version):
            self.error(BadConfig("Library version " + self._library_version + " not found in config"))
            return False
        return True

    def check_name(self) -> bool:
        if self._controller_name.lower() != self.get_from_config("Global", "Name").lower():
            self.error(BadControllerName(self._controller_name, self._library_version,
                                         self._firmware_version, self._firmwares))
            return False
        return True

    def check_firmware(self) -> bool:
        ok = False
        for opt in self._config.options(self._library_version):
            firmware_version = self.get_from_config(self._library_version, opt)
            self._firmwares.append(firmware_version)

            if _check_version(firmware_version, self._firmware_version):
                ok = True

        if not ok:
            self.error(BadFirmwareVersion(self._controller_name, self._library_version,
                                          self._firmware_version, self._firmwares))

        return ok

    @property
    def status(self):
        return self._all_ok

    @property
    def all_firmwares(self):
        return self._firmwares

    @property
    def firmware_version(self):
        return self._firmware_version

    @property
    def library_version(self):
        return self._library_version

    @property
    def name(self):
        return self._controller_name

    def checking_chain(self):
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


def open_device_safe(uri: str, klass: type, conf: str, log, force_open=False):
    """
    Function open device safe: check versions of firmware, library and program soft
    This function works similarly to open_device, but checks device name and protocol compatibility
    In case of failure (and if force_open is set to False) device will be closed
    :param uri: path to device, str (like in open_device function)
    :param klass: device handle, class
    :param conf: path to config file, str
    :param log: logging callback, Callable[int, str, int]
    :param force_open: device will be opened despite the errors
    :return: device (device handle exemplar)
    :return: status (ok/not-ok)(bool)
    :return: device name (str)
    :return: library version (str)
    :return: firmware version (str)
    :return: all supported firmware versions (List[str])
    """

    device = klass(uri, defer_open=True)
    manager = _OpenManager(device, conf, log, force_open)
    manager.checking_chain()

    return device, manager.status, manager.name, manager.library_version, manager.firmware_version, \
        manager.all_firmwares
