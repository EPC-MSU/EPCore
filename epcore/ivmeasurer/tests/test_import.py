import unittest


class ImportTest(unittest.TestCase):

    def test_import_asa(self):
        from epcore.ivmeasurer import IVMeasurerASA
        self.assertTrue(bool(IVMeasurerASA))

    def test_import_ivm02(self):
        from epcore.ivmeasurer import IVMeasurerIVM02
        self.assertTrue(bool(IVMeasurerIVM02))

    def test_import_ivm10(self):
        from epcore.ivmeasurer import IVMeasurerIVM10
        self.assertTrue(bool(IVMeasurerIVM10))
