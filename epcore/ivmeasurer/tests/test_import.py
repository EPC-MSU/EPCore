import unittest


class ImportTest(unittest.TestCase):

    def test_import_asa(self) -> None:
        from epcore.ivmeasurer import IVMeasurerASA
        self.assertTrue(bool(IVMeasurerASA))

    def test_import_bad_virtual(self) -> None:
        from epcore.ivmeasurer import IVMeasurerVirtualBad
        self.assertTrue(bool(IVMeasurerVirtualBad))

    def test_import_ivm02(self) -> None:
        from epcore.ivmeasurer import IVMeasurerIVM02
        self.assertTrue(bool(IVMeasurerIVM02))

    def test_import_ivm10(self) -> None:
        from epcore.ivmeasurer import IVMeasurerIVM10
        self.assertTrue(bool(IVMeasurerIVM10))

    def test_import_virtual(self) -> None:
        from epcore.ivmeasurer import IVMeasurerVirtual
        self.assertTrue(bool(IVMeasurerVirtual))
