"""
File with class for virtual multiplexer.
"""

import copy
from typing import Optional
from epcore.analogmultiplexer.base import (AnalogMultiplexerBase, MAX_CHANNEL_NUMBER, MIN_CHANNEL_NUMBER,
                                           ModuleTypes, MultiplexerIdentityInformation)
from epcore.elements import MultiplexerOutput


class AnalogMultiplexerVirtual(AnalogMultiplexerBase):
    """
    Class for virtual multiplexer.
    """

    NUMBER_OF_MODULES = 3

    def __init__(self, url: str, defer_open: bool = False):
        """
        :param url: URL for device identification in computer system. For serial devices
        URL will be "com:\\\\.\\COMx" (for Windows) or com:///dev/ttyACMx" (for Linux);
        :param defer_open: if True, device will not be opened upon initialization.
        """

        super().__init__(url, defer_open)
        self._chain_structure = [ModuleTypes.MODULE_TYPE_A for _ in range(self.NUMBER_OF_MODULES)]
        self._connected_channel: MultiplexerOutput = None
        self._is_open: bool = False
        if not defer_open:
            self.open_device()

    def close_device(self):
        """
        Method closes device.
        """

        self._is_open = False

    def connect_channel(self, multiplexer_output: MultiplexerOutput):
        """
        Method connects given channel of module of multiplexer to output (of line A).
        :param multiplexer_output: address of connected channel.
        """

        if not (1 <= multiplexer_output.module_number <= len(self._chain_structure)) or\
                not (MIN_CHANNEL_NUMBER <= multiplexer_output.channel_number <= MAX_CHANNEL_NUMBER):
            raise ValueError("Invalid module or channel number")
        self._connected_channel = MultiplexerOutput(channel_number=multiplexer_output.channel_number,
                                                    module_number=multiplexer_output.module_number)

    def disconnect_all_channels(self):
        """
        Method disconnects all channels from output.
        """

        self._connected_channel = None

    def get_identity_information(self) -> MultiplexerIdentityInformation:
        """
        Method returns identity information of multiplexer device.
        :return: identity information.
        """

        return MultiplexerIdentityInformation(
            controller_name="Virtual controller name",
            firmware_version=(1, 2, 3),
            hardware_version=(4, 5, 6),
            manufacturer="EPC MSU",
            product_name="Virtual analog multiplexer",
            reserved="Reserved field",
            serial_number=123456789)

    def get_connected_channel(self) -> Optional[MultiplexerOutput]:
        """
        Method returns address of channel connected to line A.
        :return: address of channel - module number and channel number within the module.
        """

        return copy.deepcopy(self._connected_channel)

    def open_device(self):
        """
        Method opens device.
        """

        self._is_open = True

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
