from ctypes import CDLL


class SoundPlayer:
    @staticmethod
    def play_cow():
        print("moo")

    def __init__(self):
        lib = CDLL("foo.so")
        print(lib.a())