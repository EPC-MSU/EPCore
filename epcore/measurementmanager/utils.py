"""
Auxiliary functions for measurements
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
from scipy import interpolate
from ..elements import MeasurementSettings
from ..ivmeasurer import IVMeasurerBase
from ..product import EyePointProduct, MeasurementParameter


def create_logger() -> logging.Logger:
    """
    :return: logger to find optimal parameters.
    """

    formatter = logging.Formatter("[%(asctime)s %(levelname)s] [Searcher] %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)

    _logger = logging.getLogger("searcher")
    _logger.addHandler(stream_handler)
    _logger.setLevel(logging.INFO)
    _logger.propagate = False
    return _logger


logger = create_logger()


class Searcher:
    """
    Class for searching optimal settings for measurer.
    """

    _ITERATIONS: int = 2  # number of iterations

    def __init__(self, measurer: IVMeasurerBase, params: Dict[EyePointProduct.Parameter, MeasurementParameter],
                 max_voltage: float = 12, log: bool = False) -> None:
        """
        :param measurer: IV-measurer;
        :param params: dictionary from which to get available values for probe signal frequency (and sampling rate),
        internal resistance and max voltage;
        :param max_voltage: the maximum voltage that can be set when searching for optimal parameters (option added in
        ticket #92268);
        :param log: if True, then output a log.
        """

        self._frequencies: List[int] = []
        self._rates: List[int] = []
        self._resistances: List[float] = []
        self._voltages: List[float] = []

        # Indexes of set values of frequency, resistance and voltage
        self._i_frequency: int = None
        self._i_resistance: int = None
        self._i_voltage: int = None

        self._integral: List[float] = []
        self._max_voltage: float = max_voltage
        self._measurer: IVMeasurerBase = measurer
        # If true then area under the curve will be maximized even for diodes and resistors
        self.maximize_square: bool = True

        logger.setLevel(logging.INFO if log else logging.ERROR)
        self._get_available_parameters(params)

    def _autosetup_settings(self, currents: List[float], voltages: List[float]) -> Tuple[int, int, int]:
        """
        Method calculates values for probe signal frequency, internal resistance and max voltage that should be set in
        next iteration.
        :param currents: measured currents;
        :param voltages: measured voltages.
        :return: indexes of probe
        """

        max_current = self._voltages[self._i_voltage] / self._resistances[self._i_resistance]
        i_new_resistance = self._define_resistance(currents, voltages, max_current)
        i_new_voltage = self._define_voltage(voltages)
        i_new_frequency = self._define_frequency(currents, voltages, max_current)
        return i_new_frequency, i_new_resistance, i_new_voltage

    def _create_settings(self, i_frequency: int, i_resistance: int, i_voltage: int) -> MeasurementSettings:
        """
        Method creates new measurement settings.
        :param i_frequency: index of frequency value to be set;
        :param i_resistance: index of internal resistance value to be set;
        :param i_voltage: index of voltage value to be set;
        :return: new measurement settings.
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

    def _define_frequency(self, currents: List[float], voltages: List[float], max_current: float) -> int:
        """
        :param currents: list with current values;
        :param voltages: list with voltage values;
        :param max_current: maximum current.
        :return: frequency index for the next iteration.
        """

        square = 4 * self._voltages[self._i_voltage] * max_current
        self._integral.append(abs(_integrate(voltages, currents) / square))
        i_new_frequency = self._i_frequency
        if self.maximize_square:
            if self._integral[0] < 0.003 and self._i_frequency > 1 and len(self._integral) == 1:
                # First check is made to be certain that 10 kHz is not optimal
                i_new_frequency = self._i_frequency - 2
            elif len(self._integral) == 1:
                # If it is optimal then keep the frequency (mostly optimal for diodes)
                i_new_frequency = self._i_frequency
            elif self._integral[-1] / self._integral[-2] > 1.2 and self._i_frequency > 0:
                # Second check is to determine whether frequency changes in direct ratio with integral or not
                i_new_frequency = self._i_frequency - 1
            elif self._integral[-1] / self._integral[-2] < 1 and self._i_frequency < len(self._frequencies) - 2:
                i_new_frequency = self._i_frequency + 2
        else:
            if self._integral[-1] < 0.005 and self._i_frequency > 0:
                i_new_frequency = self._i_frequency - 1
        return i_new_frequency

    def _define_resistance(self, currents: List[float], voltages: List[float], max_current: float) -> int:
        """
        :param currents: list with current values;
        :param voltages: list with voltage values;
        :param max_current: maximum current.
        :return: internal resistance index for the next iteration.
        """

        k_i = np.mean(np.abs(currents)) / max_current
        k_u = np.mean(np.abs(voltages)) / self._voltages[self._i_voltage]
        if k_i < 0.15 and self._i_resistance < len(self._resistances) - 1:
            i_new_resistance = self._i_resistance + 1
        elif k_u < 0.15 and self._i_resistance > 0:
            i_new_resistance = self._i_resistance - 1
        else:
            i_new_resistance = self._i_resistance
        return i_new_resistance

    def _define_voltage(self, voltages: List[float]) -> int:
        """
        :param voltages: list with voltage values.
        :return: voltage index for the next iteration.
        """

        i_new_voltage = self._i_voltage
        max_voltage = np.max(np.abs(voltages))
        for i, voltage in enumerate(self._voltages):
            if max_voltage < voltage <= self._max_voltage:
                i_new_voltage = i
                break
        return i_new_voltage

    def _get_available_parameters(self, params: Dict[EyePointProduct.Parameter, MeasurementParameter]) -> None:
        """
        Method gets available values for probe signal frequency (and sampling rate), internal resistance and max
        voltage.
        :param params: dictionary from which to get the available values.
        """

        # Define available probe signal frequencies and sampling rates
        self._frequencies = []
        self._rates = []
        for obj in params[EyePointProduct.Parameter.frequency].options:
            self._frequencies.append(obj.value[0])
            self._rates.append(obj.value[1])
        logger.info("Available frequency values: %s", self._frequencies)
        logger.info("Available sampling rate values: %s", self._rates)
        # Define available internal resistances
        self._resistances = [obj.value for obj in params[EyePointProduct.Parameter.sensitive].options]
        logger.info("Available internal resistance values: %s", self._resistances)
        # Define available voltages
        self._voltages = [obj.value for obj in params[EyePointProduct.Parameter.voltage].options]
        logger.info("Available max voltage values: %s", self._voltages)

    def _get_max_available_voltage_index(self) -> Optional[int]:
        """
        :return: index of the highest voltage that is less than the threshold maximum value.
        """

        for i, voltage in enumerate(self._voltages):
            if voltage > self._max_voltage:
                if i > 0:
                    return i - 1
                return None

        return len(self._voltages) - 1

    def search_optimal_settings(self) -> MeasurementSettings:
        """
        Experimental search for optimal settings for specified IV-measurer. During the search IV-measurer should be
        connected to a testing component. IV-curve with the optimal settings will have the most meaningful form.
        For example for a capacitor it should be ellipse.
        Warning! During the search a set of measurements with various settings will be performed. To avoid damage don’t
        use this function for sensitive components.
        """

        # Save initial settings. At the end we will set measurer to initial state
        initial_settings = self._measurer.get_settings()

        # Search optimal settings
        i_new_frequency = 4   # 10 kHz
        i_new_resistance = 1  # 4750 Ohm
        i_new_voltage = self._get_max_available_voltage_index()
        if i_new_voltage is None:
            return initial_settings

        for i in range(Searcher._ITERATIONS):
            logger.info("Iteration #%d", i)
            settings = self._create_settings(i_new_frequency, i_new_resistance, i_new_voltage)
            logger.info("Settings installed: %s", settings)
            self._measurer.set_settings(settings)
            iv_curve = self._measurer.measure_iv_curve()
            currents = iv_curve.currents
            voltages = iv_curve.voltages
            i_new_frequency, i_new_resistance, i_new_voltage = self._autosetup_settings(currents, voltages)

        # Set initial settings. Don't return without this!
        self._measurer.set_settings(initial_settings)
        optimal_settings = self._create_settings(i_new_frequency, i_new_resistance, i_new_voltage)
        logger.info("Optimal settings: %s", optimal_settings)
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
