import unittest


class ImportTest(unittest.TestCase):

    def test_import(self):
        from epcore.analogmultiplexer import AnalogMultiplexer
        self.assertTrue(bool(AnalogMultiplexer))
