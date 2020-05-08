import unittest


class ImportTest(unittest.TestCase):
    def test_import(self):
        from epcore.ivmeasurer import IVMeasurerIVM03
        self.assertTrue(bool(IVMeasurerIVM03))
