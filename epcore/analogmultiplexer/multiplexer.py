"""
File with class to work with multiplexer.
"""

from enum import Enum
from typing import Callable, List, Optional, Tuple
from dataclasses import dataclass
from epcore.analogmultiplexer.epmux.epmux import EpmuxDeviceHandle

MIN_CHANNEL_NUMBER = 1
MAX_CHANNEL_NUMBER = 64


def _close_on_error(func: Callable):
    """
    Decorator to handle errors when executing multiplexer methods.
    Due to the nature of the uRPC library uRPC device must be immediately
    closed after first error.
    :param func: IVMeasurerIVM10 method;
    :return: IVMeasurerIVM10 decorated method.
    """

    def handle(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except (OSError, RuntimeError) as exc:
            self.close_device()
            raise exc
    return handle


class LineTypes(Enum):
    """
    Class with line types.
    """

    TYPE_A = 1
    TYPE_B = 2


class ModuleTypes(Enum):
    """
    Class with module types.
    """

    NO_MODULE = 0
    MODULE_TYPE_A = 1
    MODULE_TYPE_AB = 2


@dataclass
class MultiplexerIdentityInformation:
    """
    Class for hardware identity information in unified format.
    """

    controller_name: str
    firmware_version: tuple
    hardware_version: tuple
    manufacturer: str
    product_name: str
    reserved: str
    serial_number: int


class Multiplexer:
    """
    Class to work with multiplexer.
    """

    def __init__(self, url: str, defer_open: bool = False):
        """
        :param url: URL for device identification in computer system. For
        serial devices URL will be "com:\\\\.\\COMx" (for Windows) or
        "com:///dev/tty/ttyACMx" (for Linux);
        :param defer_open: if True, device will not be opened upon initialization.
        """

        self._url: str = url
        self._device = EpmuxDeviceHandle(url, defer_open=True)
        if not defer_open:
            self.open_device()

    def close_device(self):
        """
        Method closes device.
        """

        try:
            self._device.close_device()
        except (OSError, RuntimeError):
            pass

    @_close_on_error
    def connect_channel(self, module_number: int, channel_number: int,
                        line_type: Optional[LineTypes] = LineTypes.TYPE_A):
        """
        Method connects given channel to output of given line.
        :param module_number: module number;
        :param channel_number: channel number inside module;
        :param line_type: type of line to which output the channel is to be connected.
        """

        chain = self.get_chain_info()
        if not (1 <= module_number <= len(chain)) or not (MIN_CHANNEL_NUMBER <= channel_number <= MAX_CHANNEL_NUMBER):
            raise ValueError("Invalid module or channel number")
        if chain[module_number] == ModuleTypes.MODULE_TYPE_A:
            if line_type == LineTypes.TYPE_A:
                self._device.set_channel_for_line_a(module_number, channel_number, "")
            else:
                raise ValueError("Invalid line type for module type A")
        elif chain[module_number] == ModuleTypes.MODULE_TYPE_AB:
            if line_type == LineTypes.TYPE_A:
                self._device.set_channel_for_line_a(module_number, channel_number, "")
            elif line_type == LineTypes.TYPE_B:
                self._device.set_channel_for_line_b(module_number, channel_number, "")
            else:
                raise ValueError("Invalid line type for module type B")

    @_close_on_error
    def disconnect_all_channels(self):
        """
        Method disconnects all channels from output.
        """

        self._device.all_channels_off()

    @_close_on_error
    def get_chain_info(self) -> List[ModuleTypes]:
        """
        Method returns information about chain.
        :return: list with types of multiplexer modules in chain.
        """

        chain = []
        structure = self._device.get_chain_structure()
        for module in structure.chain_structure:
            if int(module) == ModuleTypes.MODULE_TYPE_A.value:
                chain.append(ModuleTypes.MODULE_TYPE_A)
            elif int(module) == ModuleTypes.MODULE_TYPE_AB.value:
                chain.append(ModuleTypes.MODULE_TYPE_AB)
        return chain

    @_close_on_error
    def get_identity_information(self) -> MultiplexerIdentityInformation:
        """
        Method returns identity information of multiplexer device.
        :return: identity information.
        """

        buffer = self._device.get_identity_information()
        return MultiplexerIdentityInformation(
            controller_name=bytes(buffer.controller_name).decode("utf-8").replace("\x00", ""),
            firmware_version=(buffer.firmware_major, buffer.firmware_minor, buffer.firmware_bugfix),
            hardware_version=(buffer.hardware_major, buffer.hardware_minor, buffer.hardware_bugfix),
            manufacturer=bytes(buffer.manufacturer).decode("utf-8").replace("\x00", ""),
            product_name=bytes(buffer.product_name).decode("utf-8").replace("\x00", ""),
            reserved=bytes(buffer.controller_name).decode("utf-8").replace("\x00", ""),
            serial_number=int(buffer.serial_number))

    @_close_on_error
    def get_connected_channel(self, line_type: LineTypes = LineTypes.TYPE_A) -> Optional[Tuple]:
        """
        Method returns address of channel connected to given line.
        :param line_type: line.
        :return: address of channel - module number and channel number within the module.
        """

        buffer = None
        if line_type == LineTypes.TYPE_A:
            buffer = self._device.get_channel_for_line_a()
        elif line_type == LineTypes.TYPE_B:
            buffer = self._device.get_channel_for_line_b()
        if buffer:
            return buffer.module_number, buffer.channel_number

    @_close_on_error
    def open_device(self):
        """
        Method opens device.
        """

        self._device.open_device()

    def reconnect(self) -> bool:
        """
        Method reconnects device.
        :return: True if reconnect was successful.
        """

        self.close_device()
        try:
            self.open_device()
            return True
        except (OSError, RuntimeError):
            return False
