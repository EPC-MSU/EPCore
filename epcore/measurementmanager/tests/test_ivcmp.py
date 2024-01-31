import unittest
import numpy as np
from epcore.elements import IVCurve
from epcore.measurementmanager import IVCComparator


class TestIVCmpMethods(unittest.TestCase):

    def test_curves_with_different_amplitudes(self) -> None:
        comparator = IVCComparator()
        resistor1 = IVCurve()
        resistor2 = IVCurve()
        for i in range(IVCComparator.max_num_points):
            phase = 2 * np.pi * i / IVCComparator.max_num_points
            resistor1.voltages.append(0.5 * IVCComparator.voltage_amplitude * np.sin(phase))
            resistor1.currents.append(0.5 * IVCComparator.current_amplitude * np.sin(phase))
            resistor2.voltages.append(IVCComparator.voltage_amplitude * np.sin(phase))
            resistor2.currents.append(IVCComparator.current_amplitude * np.cos(phase))
        comparator.set_min_ivc(0.03 * IVCComparator.voltage_amplitude, 0.03 * IVCComparator.current_amplitude)
        res = comparator.compare_ivc(resistor1, resistor2)
        self.assertTrue((res - 0.99) < 0.01)

    def test_curves_with_different_lengths(self) -> None:
        """
        Different length curves comparison test.
        """

        comparator = IVCComparator()
        curve_1 = IVCurve()
        curve_2 = IVCurve()
        curve_1.voltages = (np.sin(np.linspace(0, 2 * np.pi, 20))).tolist()
        curve_1.currents = (np.sin(np.linspace(0, 2 * np.pi, 20))).tolist()
        curve_2.voltages = (np.sin(np.linspace(0, 2 * np.pi, 100))).tolist()
        curve_2.currents = (np.sin(np.linspace(0, 2 * np.pi, 100))).tolist()
        comparator.set_min_ivc(0.03 * IVCComparator.voltage_amplitude, 0.03 * IVCComparator.current_amplitude)
        res_1 = comparator.compare_ivc(curve_1, curve_2)
        res_2 = comparator.compare_ivc(curve_2, curve_1)
        self.assertTrue(np.abs(res_1 - res_2) < 0.01)

    def test_roughly_similar_curves(self) -> None:
        comparator = IVCComparator()
        resistor1 = IVCurve()
        resistor2 = IVCurve()
        for i in range(IVCComparator.max_num_points):
            phase = 2 * np.pi * i / IVCComparator.max_num_points
            resistor1.voltages.append(0.5 * IVCComparator.voltage_amplitude * np.sin(phase))
            resistor1.currents.append(0.5 * IVCComparator.current_amplitude * np.sin(phase))
            resistor2.voltages.append(0.47 * IVCComparator.voltage_amplitude * np.sin(phase))
            resistor2.currents.append(0.63 * IVCComparator.current_amplitude * np.sin(phase))
        comparator.set_min_ivc(0.03 * IVCComparator.voltage_amplitude, 0.03 * IVCComparator.current_amplitude)
        res = comparator.compare_ivc(resistor1, resistor2)
        # TODO: python compare return 0.25 (now 0.3)
        self.assertTrue((res - 0.3) < 0.01)

    def test_same_curve(self) -> None:
        comparator = IVCComparator()
        resistor = IVCurve()
        for i in range(IVCComparator.max_num_points):
            phase = 2 * np.pi * i / IVCComparator.max_num_points
            resistor.voltages.append(0.5 * IVCComparator.voltage_amplitude * np.sin(phase))
            resistor.currents.append(0.5 * IVCComparator.current_amplitude * np.sin(phase))
        res = comparator.compare_ivc(resistor, resistor)
        self.assertTrue(res < 0.01)

    def test_very_different_curves(self) -> None:
        comparator = IVCComparator()
        open_circuit = IVCurve()
        short_circuit = IVCurve()
        for i in range(IVCComparator.max_num_points):
            phase = 2 * np.pi * i / IVCComparator.max_num_points
            open_circuit.voltages.append(IVCComparator.voltage_amplitude * np.sin(phase))
            open_circuit.currents.append(0)
            short_circuit.voltages.append(0)
            short_circuit.currents.append(IVCComparator.current_amplitude * np.sin(phase))
        comparator.set_min_ivc(0.03 * IVCComparator.voltage_amplitude, 0.03 * IVCComparator.current_amplitude)
        res = comparator.compare_ivc(open_circuit, short_circuit)
        self.assertTrue((res - 0.99) < 0.01)
