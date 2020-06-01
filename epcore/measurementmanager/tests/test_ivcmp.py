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
        # TODO: here was 0.17 (now 0.3)
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
