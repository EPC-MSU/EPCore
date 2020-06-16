import unittest
from epcore.measurementmanager import IVCComparator
from epcore.elements import IVCurve
import numpy as np


class TestIVCmpMethods(unittest.TestCase):

    def test_number_one(self):
        comparator = IVCComparator()

        resistor = IVCurve()
        for i in range(IVCComparator.max_num_points):
            resistor.voltages.append(0.5 * IVCComparator.voltage_amplitude
                                     * np.sin(2 * np.pi * i / IVCComparator.max_num_points))
            resistor.currents.append(0.5 * IVCComparator.current_amplitude
                                     * np.sin(2 * np.pi * i / IVCComparator.max_num_points))

        res = comparator.compare_ivc(resistor, resistor)
        self.assertTrue(res < 0.01)

    def test_number_two(self):
        comparator = IVCComparator()

        open_circuit = IVCurve()
        short_circuit = IVCurve()
        for i in range(IVCComparator.max_num_points):
            open_circuit.voltages.append(IVCComparator.voltage_amplitude
                                         * np.sin(2 * np.pi * i / IVCComparator.max_num_points))
            open_circuit.currents.append(0)

            short_circuit.voltages.append(0)
            short_circuit.currents.append(IVCComparator.current_amplitude
                                          * np.sin(2 * np.pi * i / IVCComparator.max_num_points))

        comparator.set_min_ivc(0, 0)
        res = comparator.compare_ivc(open_circuit, short_circuit)
        self.assertTrue((res - 0.99) < 0.01)

    def test_number_three(self):
        comparator = IVCComparator()

        resistor1 = IVCurve()
        resistor2 = IVCurve()

        for i in range(IVCComparator.max_num_points):
            resistor1.voltages.append(0.5 * IVCComparator.voltage_amplitude
                                      * np.sin(2 * np.pi * i / IVCComparator.max_num_points))
            resistor1.currents.append(0.5 * IVCComparator.current_amplitude
                                      * np.sin(2 * np.pi * i / IVCComparator.max_num_points))
            resistor2.voltages.append(0.47 * IVCComparator.voltage_amplitude
                                      * np.sin(2 * np.pi * i / IVCComparator.max_num_points))
            resistor2.currents.append(0.63 * IVCComparator.current_amplitude
                                      * np.sin(2 * np.pi * i / IVCComparator.max_num_points))
        comparator.set_min_ivc(0, 0)
        res = comparator.compare_ivc(resistor1, resistor2)
        # TODO: python compare return 0.25 (now 0.3)
        self.assertTrue((res - 0.3) < 0.01)

    def test_number_four(self):
        comparator = IVCComparator()

        resistor1 = IVCurve()
        resistor2 = IVCurve()

        for i in range(IVCComparator.max_num_points):
            resistor1.voltages.append(0.5 * IVCComparator.voltage_amplitude
                                      * np.sin(2 * np.pi * i / IVCComparator.max_num_points))
            resistor1.currents.append(0.5 * IVCComparator.current_amplitude
                                      * np.sin(2 * np.pi * i / IVCComparator.max_num_points))
            resistor2.voltages.append(IVCComparator.voltage_amplitude
                                      * np.sin(2 * np.pi * i / IVCComparator.max_num_points))
            resistor2.currents.append(IVCComparator.current_amplitude
                                      * np.cos(2 * np.pi * i / IVCComparator.max_num_points))
        comparator.set_min_ivc(0, 0)
        res = comparator.compare_ivc(resistor1, resistor2)
        self.assertTrue((res - 0.99) < 0.01)

    def test_number_five(self):
        """
        Different length curves comparison test
        """
        comparator = IVCComparator()

        curve_1 = IVCurve()
        curve_2 = IVCurve()

        curve_1.voltages = (np.sin(np.linspace(0, 2 * np.pi, 20))).tolist()
        curve_1.currents = (np.sin(np.linspace(0, 2 * np.pi, 20))).tolist()

        curve_2.voltages = (np.sin(np.linspace(0, 2 * np.pi, 100))).tolist()
        curve_2.currents = (np.sin(np.linspace(0, 2 * np.pi, 100))).tolist()

        comparator.set_min_ivc(0, 0)

        res_1 = comparator.compare_ivc(curve_1, curve_2)
        res_2 = comparator.compare_ivc(curve_2, curve_1)
        self.assertTrue(np.abs(res_1 - res_2) < 0.01)
