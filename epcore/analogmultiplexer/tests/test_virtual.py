import unittest
from epcore.analogmultiplexer import AnalogMultiplexerVirtual, ModuleTypes, MultiplexerIdentityInformation
from epcore.elements import MultiplexerOutput


class TestAnalogMultiplexerVirtual(unittest.TestCase):

    def test_connect_channel_to_allowable_output(self):
        """
        Test checks connection of channel of virtual multiplexer to
        allowable output.
        """

        output = MultiplexerOutput(channel_number=33, module_number=3)
        multiplexer = AnalogMultiplexerVirtual()
        multiplexer.connect_channel(output)
        self.assertTrue(multiplexer.get_connected_channel() == output)

    def test_connect_channel_to_impermissible_output(self):
        """
        Test checks connection of channel of virtual multiplexer to
        impermissible output.
        """

        output = MultiplexerOutput(channel_number=89, module_number=3)
        multiplexer = AnalogMultiplexerVirtual()
        with self.assertRaises(ValueError):
            multiplexer.connect_channel(output)

    def test_disconnect_all_channels(self):
        """
        Test checks disconnection of all channels for virtual multiplexer.
        """

        output = MultiplexerOutput(channel_number=33, module_number=3)
        multiplexer = AnalogMultiplexerVirtual()
        multiplexer.connect_channel(output)
        self.assertTrue(multiplexer.get_connected_channel() == output)
        multiplexer.disconnect_all_channels()
        self.assertIsNone(multiplexer.get_connected_channel())

    def test_get_chain_info(self):
        """
        Test checks reading information about modules chain in virtual multiplexer.
        """

        chain = [ModuleTypes.MODULE_TYPE_A for _ in range(AnalogMultiplexerVirtual.NUMBER_OF_MODULES)]
        multiplexer = AnalogMultiplexerVirtual()
        self.assertEqual(multiplexer.get_chain_info(), chain)

    def test_get_identity_information(self):
        """
        Test checks reading identity information from virtual multiplexer.
        """

        info = MultiplexerIdentityInformation(
            controller_name="Virtual controller name",
            firmware_version=(1, 2, 3),
            hardware_version=(4, 5, 6),
            manufacturer="EPC MSU",
            product_name="Virtual analog multiplexer",
            reserved="Reserved field",
            serial_number=123456789)
        multiplexer = AnalogMultiplexerVirtual()
        self.assertEqual(multiplexer.get_identity_information(), info)

    def test_is_correct_output(self):
        """
        Test checks that virtual multiplexer correctly determines valid and invalid outputs.
        """

        multiplexer = AnalogMultiplexerVirtual()
        correct_output = MultiplexerOutput(channel_number=33, module_number=2)
        self.assertTrue(multiplexer.is_correct_output(correct_output))
        uncorrect_output = MultiplexerOutput(channel_number=69, module_number=2)
        self.assertFalse(multiplexer.is_correct_output(uncorrect_output))
