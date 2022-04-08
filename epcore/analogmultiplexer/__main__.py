"""
File with an example of how to use the analogmutliplexer module.
"""

import argparse
from .multiplexer import LineTypes, Multiplexer


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="Real multiplexer COM port. Format: com:\\\\.\\COMx or com:///dev/ttyACMx",
                        type=str)
    args = parser.parse_args()

    multiplexer = Multiplexer(args.url, defer_open=True)
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
    try:
        multiplexer.connect_channel(module_number_to_connect, channel_number_to_connect)
        print(f"Channel {module_number_to_connect}.{channel_number_to_connect} connected")
    except Exception as exc:
        print(f"Failed to connect channel {module_number_to_connect}.{channel_number_to_connect}")
    try:
        line_to_connect = LineTypes.TYPE_B
        multiplexer.connect_channel(module_number_to_connect, channel_number_to_connect, line_to_connect)
        print(f"Channel {module_number_to_connect}.{channel_number_to_connect} connected")
    except Exception as exc:
        print(f"Failed to connect channel {module_number_to_connect}.{channel_number_to_connect}")
    # Disconnect all channels
    multiplexer.disconnect_all_channels()
    print("All channels disconnected")
