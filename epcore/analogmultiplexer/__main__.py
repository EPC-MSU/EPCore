"""
File with an example of how to use the analogmutliplexer module.
"""

import argparse
from epcore.analogmultiplexer import AnalogMultiplexer, AnalogMultiplexerVirtual
from epcore.elements import MultiplexerOutput


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="Real multiplexer COM port. Format: com:\\\\.\\COMx or com:///dev/ttyACMx",
                        type=str)
    args = parser.parse_args()

    if args.url == "virtual":
        multiplexer = AnalogMultiplexerVirtual(args.url, defer_open=True)
    else:
        multiplexer = AnalogMultiplexer(args.url, defer_open=True)
    multiplexer.open_device()
    # Get identity information of multiplexer and print it
    multiplexer_info = multiplexer.get_identity_information()
    print(multiplexer_info)
    # Get information about multiplexer chain
    chain = multiplexer.get_chain_info()
    print(chain)
    # Connect channel to output
    module_number_to_connect = 1
    channel_number_to_connect = 1
    multiplexer_output = MultiplexerOutput(channel_number=channel_number_to_connect,
                                           module_number=module_number_to_connect)
    try:
        multiplexer.connect_channel(multiplexer_output)
        connected_channel = multiplexer.get_connected_channel()
        print(f"Channel {connected_channel.channel_number} on module {connected_channel.module_number} was connected")
    except Exception as exc:
        print(f"Failed to connect channel {channel_number_to_connect} on module {module_number_to_connect}: {exc}")
    # Disconnect all channels
    multiplexer.disconnect_all_channels()
    print("All channels disconnected")
