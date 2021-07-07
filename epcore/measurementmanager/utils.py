"""
Auxiliary functions for measurements
"""

from typing import Dict, List, Tuple
import numpy as np
from scipy import interpolate
from ..elements import MeasurementSettings
from ..ivmeasurer import IVMeasurerBase
from ..product import EPLab


class Searcher:
    """
    Class for searching optimal settings for measurer.
    """

    _ITERATIONS = 3  # number of iterations

    def __init__(self, measurer: IVMeasurerBase, params: Dict):
        """
        :param measurer:
        :param params: object from which to get available values for probe
        signal frequency (and sampling rate), internal resistance and max
        voltage.
        """

        self._measurer = measurer
        # If true then area under the curve will be maximized even for diodes
        # and resistors
        self.maximize_square = True
        # Indexes of set values of frequency, resistance and voltage
        self._i_frequency: int = None
        self._i_resistance: int = None
        self._i_voltage: int = None
        self._get_available_parameters(params)
        self._integral: List[float] = []

    def _autosetup_settings(self, currents: List[float],
                            voltages: List[float]) -> Tuple[int, int, int]:
        """
        Method calculates values for probe signal frequency, internal
        resistance and max voltage that should be set in next iteration.
        :param currents: measured currents;
        :param voltages: measured voltages.
        :return: indexes of probe
        """

        # Get current settings
        max_current = self._voltages[self._i_voltage] / self._resistances[self._i_resistance]
        # Change current
        c_avg = np.mean(np.abs(currents)) / max_current
        v_avg = np.mean(np.abs(voltages)) / self._voltages[self._i_voltage]
        if c_avg < 0.15 and self._i_resistance < len(self._resistances) - 1:
            i_new_resistance = self._i_resistance + 1
        elif v_avg < 0.15 and self._i_resistance > 0:
            i_new_resistance = self._i_resistance - 1
        else:
            i_new_resistance = self._i_resistance
        # Change voltage
        i_new_voltage = self._i_voltage
        max_voltage = np.max(np.abs(voltages))
        for i, voltage in enumerate(self._voltages):
            if max_voltage < voltage:
                i_new_voltage = i
                break
        # Change frequency algorithm for ITER = 3
        square = (self._voltages[self._i_voltage] * 2) * (max_current * 2)
        self._integral.append(abs(_integrate(voltages, currents) / square))
        i_new_frequency = self._i_frequency
        if self.maximize_square:
            # First check is made to be certain that 10kHz is not optimal
            if (self._integral[0] < 0.003 and self._i_frequency > 1 and
                    len(self._integral) == 1):
                i_new_frequency = self._i_frequency - 2
            # If it is optimal then keep the frequency (mostly optimal
            # for diodes)
            elif len(self._integral) == 1:
                i_new_frequency = self._i_frequency
            # Second check is to determine whether frequency changes in direct
            # ratio with integral or not
            elif (self._integral[-1] / self._integral[-2] > 1.2 and
                  self._i_frequency > 0):
                i_new_frequency = self._i_frequency - 1
            elif (self._integral[-1] / self._integral[-2] < 1 and
                  self._i_frequency < len(self._frequencies) - 2):
                i_new_frequency = self._i_frequency + 2
        else:
            if self._integral[-1] < 0.05 and self._i_frequency > 0:
                i_new_frequency = self._i_frequency - 1
        return i_new_frequency, i_new_resistance, i_new_voltage

    def _get_available_parameters(self, params: Dict):
        """
        Method gets available values for probe signal frequency (and sampling
        rate), internal resistance and max voltage.
        :param params: object from which to get the values.
        :return: tuple of available probe signal frequencies, sampling rates,
        internal resistances and max voltages.
        """

        # Define available probe signal frequencies and sampling rates
        self._frequencies = []
        self._rates = []
        for obj in params[EPLab.Parameter.frequency].options:
            self._frequencies.append(obj.value[0])
            self._rates.append(obj.value[1])
        # Define available internal resistances
        self._resistances = [obj.value for obj in params[EPLab.Parameter.sensitive].options]
        # Define available voltages
        self._voltages = [obj.value for obj in params[EPLab.Parameter.voltage].options]

    def _set_settings(self, i_frequency: int, i_resistance: int,
                      i_voltage: int) -> MeasurementSettings:
        """
        Method sets values for measurement settings.
        :param i_frequency: index of frequency value to be set;
        :param i_resistance: index of internal resistance value to be set;
        :param i_voltage: index of voltage value to be set;
        :return: measurement settings.
        """

        settings = MeasurementSettings(
            sampling_rate=self._rates[i_frequency],
            probe_signal_frequency=self._frequencies[i_frequency],
            internal_resistance=self._resistances[i_resistance],
            max_voltage=self._voltages[i_voltage]
        )
        self._i_frequency = i_frequency
        self._i_resistance = i_resistance
        self._i_voltage = i_voltage
        return settings

    def search_optimal_settings(self) -> MeasurementSettings:
        """
        Experimental search for optimal settings for specified IVMeasurer.
        During the search IVMeasurer should be connected to a testing
        component. IVCurve with the optimal settings will have the most
        meaningful form. For example for a capacitor it should be ellipse.
        Warning! During the search a set of measurements with various
        settings will be performed. To avoid damage don’t use this function
        for sensitive components.
        """

        # Save initial settings. At the end we will set measurer to initial
        # state
        initial_settings = self._measurer.get_settings()
        # Search optimal settings
        i_new_frequency = 4
        i_new_resistance = 1
        i_new_voltage = 3
        for _ in range(1, self._ITERATIONS):
            settings = self._set_settings(i_new_frequency, i_new_resistance,
                                          i_new_voltage)
            self._measurer.set_settings(settings)
            v_c = self._measurer.measure_iv_curve()
            currents = v_c.currents
            voltages = v_c.voltages
            (i_new_frequency, i_new_resistance, i_new_voltage) =\
                self._autosetup_settings(currents, voltages)
        # Set initial settings. Don't return without this!
        self._measurer.set_settings(initial_settings)
        optimal_settings = self._set_settings(i_new_frequency, i_new_resistance,
                                              i_new_voltage)
        return optimal_settings


def _equidistant(voltages: List[float], currents: List[float]) -> np.array:
    """
    :param voltages: measured voltages;
    :param currents: measured currents.
    :return:
    """

    # There are some repeats...
    an = np.array([voltages, currents])
    params = np.arange(0, 1, 1.0 / len(an[0]))
    tck, _ = interpolate.splprep(an, u=params, s=0.00)
    eq = np.array(interpolate.splev(params, tck))
    return eq


def _integrate(voltages: List[float], currents: List[float]) -> float:
    """
    Function calculates area of closed loop.
    :param voltages: measured voltages;
    :param currents: measured currents.
    :return: area.
    """

    eq = _equidistant(voltages, currents)
    area = np.dot(np.diff(np.append(eq[0], eq[0][0])), eq[1])
    return area
