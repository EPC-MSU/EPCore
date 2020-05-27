# This module test libivcmp work and check correct work of binding
from __future__ import print_function
import unittest
from libivcmp import IvCurve, CompareIvc, MAX_NUM_POINTS, SetMinVC, VOLTAGE_AMPL, CURRENT_AMPL
from ctypes import c_double
import numpy as np


class TestStringMethods(unittest.TestCase):

    def test_number_one(self):
        self.IVCResistor1 = IvCurve()
        for i in range(MAX_NUM_POINTS):
            self.IVCResistor1.voltages[i] = c_double(0.5 * VOLTAGE_AMPL * np.sin(2 * np.pi * i / MAX_NUM_POINTS))
            self.IVCResistor1.currents[i] = c_double(0.5 * CURRENT_AMPL * np.sin(2 * np.pi * i / MAX_NUM_POINTS))
        SetMinVC(0, 0)
        res = CompareIvc(self.IVCResistor1, self.IVCResistor1, MAX_NUM_POINTS)
        self.assertTrue(res < 0.1)

    def test_number_two(self):
        self.IVCOpenCircuit = IvCurve()
        self.IVCShortCircuit = IvCurve()
        for i in range(MAX_NUM_POINTS):
            self.IVCOpenCircuit.voltages[i] = c_double(VOLTAGE_AMPL * np.sin(2 * np.pi * i / MAX_NUM_POINTS))
            self.IVCOpenCircuit.currents[i] = c_double(0)
            self.IVCShortCircuit.voltages[i] = c_double(0)
            self.IVCShortCircuit.currents[i] = c_double(CURRENT_AMPL * np.sin(2 * np.pi * i / MAX_NUM_POINTS))
        SetMinVC(0, 0)
        res = CompareIvc(self.IVCShortCircuit, self.IVCOpenCircuit, MAX_NUM_POINTS)
        self.assertTrue((res - 1.) < 0.1)

    def test_number_three(self):
        self.IVCResistor1 = IvCurve()
        self.IVCResistor2 = IvCurve()
        for i in range(MAX_NUM_POINTS):
            self.IVCResistor1.voltages[i] = c_double(0.5 * VOLTAGE_AMPL * np.sin(2 * np.pi * i / MAX_NUM_POINTS))
            self.IVCResistor1.currents[i] = c_double(0.5 * CURRENT_AMPL * np.sin(2 * np.pi * i / MAX_NUM_POINTS))
            self.IVCResistor2.voltages[i] = c_double(0.47 * VOLTAGE_AMPL * np.sin(2 * np.pi * i / MAX_NUM_POINTS))
            self.IVCResistor2.currents[i] = c_double(0.63 * CURRENT_AMPL * np.sin(2 * np.pi * i / MAX_NUM_POINTS))
        res = CompareIvc(self.IVCResistor1, self.IVCResistor2, MAX_NUM_POINTS)
        self.assertTrue((res - 0.18) < 0.1)

    def test_number_four(self):
        self.IVCResistor1 = IvCurve()
        self.IVCCapacitor = IvCurve()
        for i in range(MAX_NUM_POINTS):
            self.IVCResistor1.voltages[i] = 0.5 * VOLTAGE_AMPL * np.sin(2 * np.pi * i / MAX_NUM_POINTS)
            self.IVCResistor1.currents[i] = 0.5 * CURRENT_AMPL * np.sin(2 * np.pi * i / MAX_NUM_POINTS)
            self.IVCCapacitor.voltages[i] = VOLTAGE_AMPL * np.sin(2 * np.pi * i / MAX_NUM_POINTS)
            self.IVCCapacitor.currents[i] = CURRENT_AMPL * np.cos(2 * np.pi * i / MAX_NUM_POINTS)
        SetMinVC(0, 0)
        res = CompareIvc(self.IVCResistor1, self.IVCCapacitor, MAX_NUM_POINTS)
        self.assertTrue((res - 1.) < 0.1)


if __name__ == "__main__":
    unittest.main()
