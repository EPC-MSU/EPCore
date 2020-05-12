import unittest


class ImportTest(unittest.TestCase):
    def test_import(self):
        from epcore.ivmeasurer import IVMeasurerIVM10
        self.assertTrue(bool(IVMeasurerIVM10))
