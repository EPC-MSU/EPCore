"""
File with data for measurement settings of Meridian device.
"""

import logging
import math
from enum import IntEnum
from typing import Dict, KeysView
from dataclasses import dataclass


def calculate_frequency(f_dd) -> float:
    """
    Function calculates sampling frequency.
    :param f_dd:
    :return:
    """

    f_dr = 2 ** (- math.ceil(math.log2(2e8 / f_dd))) * 2e8
    if f_dr >= 100000000.0:  # PicoScope max sampling frequency
        f_dr = 100000000.0
    if f_dr != f_dd:
        logging.info(
            "PicoScope device does not support sampling frequency: %s\n"
            "Setting the closest supported sampling frequency: %s\n",
            str(f_dd), str(f_dr))
    return f_dr


class _Frequency(IntEnum):
    """
    Class with frequency modes.
    """

    FREQUENCY_1HZ = 0
    FREQUENCY_5HZ = 1
    FREQUENCY_10HZ = 2
    FREQUENCY_50HZ = 3
    FREQUENCY_100HZ = 4
    FREQUENCY_400HZ = 5
    FREQUENCY_1_5KHZ = 6
    FREQUENCY_6KHZ = 7
    FREQUENCY_25KHZ = 8
    FREQUENCY_100KHZ = 9
    FREQUENCY_400KHZ = 10
    FREQUENCY_1_5MHZ = 11
    FREQUENCY_3MHZ = 12
    FREQUENCY_6MHZ = 13
    FREQUENCY_12MHZ = 14


# Frequency mode to (sampling frequency, probe signal frequency)
_frequency_to_mode = {
    _Frequency.FREQUENCY_1HZ: (100.0, 1.0),
    _Frequency.FREQUENCY_5HZ: (500.0, 5.0),
    _Frequency.FREQUENCY_10HZ: (1000.0, 10.0),
    _Frequency.FREQUENCY_50HZ: (5000.0, 50.0),
    _Frequency.FREQUENCY_100HZ: (10000.0, 100.0),
    _Frequency.FREQUENCY_400HZ: (40000.0, 400.0),
    _Frequency.FREQUENCY_1_5KHZ: (150000.0, 1500.0),
    _Frequency.FREQUENCY_6KHZ: (600000.0, 6000.0),
    _Frequency.FREQUENCY_25KHZ: (2500000.0, 25000.0),
    _Frequency.FREQUENCY_100KHZ: (10000000.0, 100000.0),
    _Frequency.FREQUENCY_400KHZ: (40000000.0, 400000.0),
    _Frequency.FREQUENCY_1_5MHZ: (150000000.0, 1500000.0),
    _Frequency.FREQUENCY_3MHZ: (300000000.0, 3000000.0),
    _Frequency.FREQUENCY_6MHZ: (600000000.0, 6000000.0),
    _Frequency.FREQUENCY_12MHZ: (1200000000.0, 12000000.0)}

# Frequency mode to label
_frequency_to_label = {
    _Frequency.FREQUENCY_1HZ: "1 Hz",
    _Frequency.FREQUENCY_5HZ: "5 Hz",
    _Frequency.FREQUENCY_10HZ: "10 Hz",
    _Frequency.FREQUENCY_50HZ: "50 Hz",
    _Frequency.FREQUENCY_100HZ: "100 Hz",
    _Frequency.FREQUENCY_400HZ: "400 Hz",
    _Frequency.FREQUENCY_1_5KHZ: "1.5 kHz",
    _Frequency.FREQUENCY_6KHZ: "6 kHz",
    _Frequency.FREQUENCY_25KHZ: "25 kHz",
    _Frequency.FREQUENCY_100KHZ: "100 kHz",
    _Frequency.FREQUENCY_400KHZ: "400 kHz",
    _Frequency.FREQUENCY_1_5MHZ: "1.5 MHz",
    _Frequency.FREQUENCY_3MHZ: "3 MHz",
    _Frequency.FREQUENCY_6MHZ: "6 MHz",
    _Frequency.FREQUENCY_12MHZ: "12 MHz"}


class _Current(IntEnum):
    """
    Class with current modes.
    """

    CURRENT_0_5MA = 0
    CURRENT_1MA = 1
    CURRENT_5MA = 2
    CURRENT_10MA = 3
    CURRENT_15MA = 4
    CURRENT_2MA = 5
    CURRENT_25MA = 6
    CURRENT_50MA = 7
    CURRENT_75MA = 8
    CURRENT_90MA = 9


# Max current mode to measurement settings value
_current_to_ms = {
    _Current.CURRENT_0_5MA: 0.5,
    _Current.CURRENT_1MA: 1,
    _Current.CURRENT_5MA: 5,
    _Current.CURRENT_10MA: 10,
    _Current.CURRENT_15MA: 15,
    _Current.CURRENT_2MA: 2,
    _Current.CURRENT_25MA: 25,
    _Current.CURRENT_50MA: 50,
    _Current.CURRENT_75MA: 75,
    _Current.CURRENT_90MA: 90}

# Max current mode to label
_current_to_label = {
    _Current.CURRENT_0_5MA: "0.5 mA",
    _Current.CURRENT_1MA: "1 mA",
    _Current.CURRENT_5MA: "5 mA",
    _Current.CURRENT_10MA: "10 mA",
    _Current.CURRENT_15MA: "15 mA",
    _Current.CURRENT_2MA: "2 mA",
    _Current.CURRENT_25MA: "25 mA",
    _Current.CURRENT_50MA: "50 mA",
    _Current.CURRENT_75MA: "75 mA",
    _Current.CURRENT_90MA: "90 mA"}


class _Voltage(IntEnum):
    """
    Class with voltage modes.
    """

    VOLTAGE_1V = 0
    VOLTAGE_1_5V = 1
    VOLTAGE_2V = 2
    VOLTAGE_2_5V = 3
    VOLTAGE_3V = 4
    VOLTAGE_4V = 5
    VOLTAGE_4_5V = 6
    VOLTAGE_5V = 7
    VOLTAGE_6V = 8
    VOLTAGE_6_7V = 9
    VOLTAGE_7_5V = 10
    VOLTAGE_10V = 11


# Voltage mode to measurement settings value
_voltage_to_ms = {
    _Voltage.VOLTAGE_1V: 1.,
    _Voltage.VOLTAGE_1_5V: 1.5,
    _Voltage.VOLTAGE_2V: 2.,
    _Voltage.VOLTAGE_2_5V: 2.5,
    _Voltage.VOLTAGE_3V: 3.,
    _Voltage.VOLTAGE_4V: 4.,
    _Voltage.VOLTAGE_4_5V: 4.5,
    _Voltage.VOLTAGE_5V: 5.0,
    _Voltage.VOLTAGE_6V: 6.0,
    _Voltage.VOLTAGE_6_7V: 6.7,
    _Voltage.VOLTAGE_7_5V: 7.5,
    _Voltage.VOLTAGE_10V: 10.}

# Voltage mode to label
_voltage_to_label = {
    _Voltage.VOLTAGE_1V: "1 V",
    _Voltage.VOLTAGE_1_5V: "1.5 V",
    _Voltage.VOLTAGE_2V: "2 V",
    _Voltage.VOLTAGE_2_5V: "2.5 V",
    _Voltage.VOLTAGE_3V: "3 V",
    _Voltage.VOLTAGE_4V: "4 V",
    _Voltage.VOLTAGE_4_5V: "4.5 V",
    _Voltage.VOLTAGE_5V: "5 V",
    _Voltage.VOLTAGE_6V: "6 V",
    _Voltage.VOLTAGE_6_7V: "6.7 V",
    _Voltage.VOLTAGE_7_5V: "7.5 V",
    _Voltage.VOLTAGE_10V: "10 V"}

_n_points = 512  # n_points in real mode must be 512 or 256
_flags = 1  # this parameter do not affect for curve

CalibrationTypes = {"Быстрая калибровка. Замкнутые щупы": 0,
                    "Быстрая калибровка. Разомкнутые щупы": 1,
                    "Полная калибровка. Замкнутые щупы": 2,
                    "Полная калибровка. Разомкнутые щупы": 3}


@dataclass
class MeasurementSettings:
    """
    Measurement settings for Meridian device.
    """

    sampling_rate: float
    probe_signal_frequency: float
    max_voltage: float
    max_current: float
    n_points: int
    n_charge_points: int
    flags: int
    model_type: str
    model_nominal: 0
    mode: str

    def get_attribute_names(self) -> KeysView:
        """
        Method returns names of attributes in class.
        :return: names of attributes.
        """

        return self.__dict__.keys()

    def get_value(self, filed_name: str):
        """
        Method returns value of attribute by given name.
        :param filed_name: name of attribute.
        :return: value of attribute.
        """

        return getattr(self, filed_name, None)

    def to_json(self) -> Dict:
        """
        Method returns object as dictionary.
        """

        json_data = {
            "sampling_rate": self.sampling_rate,
            "probe_signal_frequency": self.probe_signal_frequency,
            "max_voltage": self.max_voltage,
            "max_current": self.max_current,
            "n_points": self.n_points,
            "n_charge_points": self.n_charge_points,
            "flags": self.flags,
            "model_type": self.model_type,
            "model_nominal": self.model_nominal,
            "mode": self.mode}
        return json_data
