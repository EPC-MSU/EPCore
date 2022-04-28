"""
File with class to work with real analog multiplexer device.
"""

from typing import Optional
from epcore.analogmultiplexer.base import (AnalogMultiplexerBase, BadMultiplexerOutputError, close_on_error,
                                           MAX_CHANNEL_NUMBER, MIN_CHANNEL_NUMBER, ModuleTypes,
                                           MultiplexerIdentityInformation)
from epcore.analogmultiplexer.epmux.epmux import EpmuxDeviceHandle
from epcore.elements import MultiplexerOutput


class AnalogMultiplexer(AnalogMultiplexerBase):
    """
    Class to work with multiplexer.
    """

    def __init__(self, url: str, defer_open: bool = False):
        """
        :param url: URL for device identification in computer system. For serial devices
        URL will be "com:\\\\.\\COMx" (for Windows) or com:///dev/ttyACMx" (for Linux);
        :param defer_open: if True, device will not be opened upon initialization.
        """

        super().__init__(url, defer_open)
        self._device: EpmuxDeviceHandle = EpmuxDeviceHandle(url, defer_open=True)
        if not defer_open:
            self.open_device()

    def _get_chain_info(self):
        """
        Method reads information about chain from multiplexer device.
        """

        self._chain_structure = []
        structure = self._device.get_chain_structure()
        for module in structure.chain_structure:
            if int(module) == ModuleTypes.MODULE_TYPE_A.value:
                self._chain_structure.append(ModuleTypes.MODULE_TYPE_A)
            elif int(module) == ModuleTypes.MODULE_TYPE_AB.value:
                self._chain_structure.append(ModuleTypes.MODULE_TYPE_AB)

    def close_device(self):
        """
        Method closes device.
        """

        try:
            self._device.close_device()
        except (OSError, RuntimeError):
            pass

    @close_on_error
    def connect_channel(self, multiplexer_output: MultiplexerOutput):
        """
        Method connects given channel of module of multiplexer to output (of line A).
        :param multiplexer_output: address of connected channel.
        """

        if not (1 <= multiplexer_output.module_number <= len(self._chain_structure)) or\
                not (MIN_CHANNEL_NUMBER <= multiplexer_output.channel_number <= MAX_CHANNEL_NUMBER):
            raise BadMultiplexerOutputError("Invalid module or channel number")
        self._device.set_channel_for_line_a(multiplexer_output.module_number, multiplexer_output.channel_number, "")

    @close_on_error
    def disconnect_all_channels(self):
        """
        Method disconnects all channels from output.
        """

        self._device.all_channels_off()

    @close_on_error
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

    @close_on_error
    def get_connected_channel(self) -> Optional[MultiplexerOutput]:
        """
        Method returns address of channel connected to line A.
        :return: address of channel - module number and channel number within the module.
        """

        buffer = self._device.get_channel_for_line_a()
        if buffer:
            return MultiplexerOutput(channel_number=buffer.channel_number, module_number=buffer.module_number)
        return None

    @close_on_error
    def open_device(self):
        """
        Method opens device.
        """

        self._device.open_device()
        self._get_chain_info()

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
