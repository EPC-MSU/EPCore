# Example here

from argparse import ArgumentParser
from ..pin import Pin
from .filemanager import save


if __name__ == "__main__":
    parser = ArgumentParser(description="FileManager example!")
    parser.add_argument("foo", type=int, help="just integer")

    args = parser.parse_args()
    print(args.foo)
    save([Pin(), Pin()])
