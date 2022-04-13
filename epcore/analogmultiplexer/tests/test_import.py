import unittest


class ImportTest(unittest.TestCase):

    def test_import(self):
        from epcore.analogmultiplexer import Multiplexer
        self.assertTrue(bool(Multiplexer))
