from ctypes import CDLL
from os.path import join, dirname


libpath = join(dirname(__file__), "foo.so")


class SoundPlayer:
    @staticmethod
    def play_cow():
        print("moo")

    def __init__(self):
        lib = CDLL(libpath)
        print(lib.get_foo())
