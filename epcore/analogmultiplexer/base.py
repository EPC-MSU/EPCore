"""
File with base class for multiplexer.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, List, Optional
from dataclasses import dataclass
from epcore.elements import MultiplexerOutput

# Minimum and maximum number of channels in one module
MIN_CHANNEL_NUMBER = 1
MAX_CHANNEL_NUMBER = 64


def close_on_error(func: Callable):
    """
    Decorator to handle errors when executing multiplexer methods.
    Due to the nature of the uRPC library uRPC device must be immediately
    closed after first error.
    :param func: decorated method.
    :return: wrapper.
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


class AnalogMultiplexerBase(ABC):
    """
    Base class for multiplexer to implement standard interface.
    """

    def __init__(self, url: str, defer_open: bool = False):
        """
        :param url: URL for device identification in computer system. For serial devices
        URL will be "com:\\\\.\\COMx" (for Windows) or com:///dev/ttyACMx" (for Linux);
        :param defer_open: if True, device will not be opened upon initialization.
        """

        self._chain_structure: list = []
        self._url: str = url

    @abstractmethod
    def close_device(self):
        """
        Method closes device.
        """

        raise NotImplementedError()

    @abstractmethod
    def connect_channel(self, multiplexer_output: MultiplexerOutput):
        """
        Method connects given channel of module of multiplexer to output (of line A).
        :param multiplexer_output: address of connected channel.
        """

        raise NotImplementedError()

    @abstractmethod
    def disconnect_all_channels(self):
        """
        Method disconnects all channels from output.
        """

        raise NotImplementedError()

    @close_on_error
    def get_chain_info(self) -> List[ModuleTypes]:
        """
        Method returns information about chain.
        :return: list with types of multiplexer modules in chain.
        """

        return self._chain_structure

    @abstractmethod
    def get_identity_information(self) -> MultiplexerIdentityInformation:
        """
        Method returns identity information of multiplexer device.
        :return: identity information.
        """

        raise NotImplementedError

    @abstractmethod
    def get_connected_channel(self) -> Optional[MultiplexerOutput]:
        """
        Method returns address of channel connected to line A.
        :return: address of channel - module number and channel number within the module.
        """

        raise NotImplementedError

    @abstractmethod
    def open_device(self):
        """
        Method opens device.
        """

        raise NotImplementedError

    def reconnect(self) -> bool:
        """
        Method reconnects device.
        :return: True if reconnection was successful.
        """

        self.close_device()
        try:
            self.open_device()
            return True
        except (OSError, RuntimeError):
            return False
