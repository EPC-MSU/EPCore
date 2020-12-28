from dataclasses import dataclass
from abc import abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from epcore.measurementmanager import MeasurementSystem
from epcore.elements import MeasurementSettings
from warnings import warn
import numpy as np
from enum import Enum, auto


@dataclass
class MeasurementParameterOption:
    name: str
    value: Any
    label_ru: str
    label_en: str


@dataclass
class MeasurementParameter:
    name: Enum
    label_ru: str
    label_en: str
    options: List[MeasurementParameterOption]


class ProductBase:
    """
    This class defines the whole system functionality.
    If you want to add additional information, limitations or
    change behavior for some methods, simply derive an other class
    for your product from this base class.
    """
    _precision = 0.01

    def __init__(self, msystem: MeasurementSystem):
        self.msystem = msystem
        self.mparams = {}

    @classmethod
    def create_from_json(cls, json: Dict) -> "ProductBase":
        raise NotImplementedError()  # TODO: this

    @abstractmethod
    def get_current_options(self) -> Dict[Enum, str]:
        """
        This function can be used for setting lists and radiobuttons
        in GUI for current settings.
        This function:
        * Get current settings from measurement system
        * Find correct option for all parameters for current settings
        * return options to be set in GUI
        If for some parameters there is now Option in option list,
        empty Option should be returned and warning should be printed to log.
        """
        raise NotImplementedError()

    def get_all_available_options(self) -> Dict[Enum, MeasurementParameter]:
        """
        This function returns all parameters and all available options.
        If you have a state machine and from current state
        only subset of options is available,
        you should redefine this function and add additional logic here.
        """
        return self.mparams

    @abstractmethod
    def set_settings_from_options(self, params: Dict[Enum, str]):
        """
        This function accepts dict of options and set settings to measurement system.
        In case there is no options for some parameters, they should keep their old value.
        So if you call set_settings_from_options({"probe_signal_frequency": (...)}),
        it means that probe signal frequency should be changed while
        voltage and internal resistance should stay unchanged.
        If you want to add additional limitations for parameter combinations in your product,
        redefine this function.
        """
        raise NotImplementedError()

    def adjust_plot_scale(self, settings: Optional[MeasurementSettings] = None) -> Tuple[float, float]:
        """
        You can use this function for
        setting IVCurve plot scale for current setting.
        By default it returns:
        voltage = max_voltage * 1.2
        current = max_voltage / internal_resistance * 1.2
        If you want to adjust the scale for some modes,
        you should redefine this function.
        Note! This function return value in A,
        but you probably will plot current in mA,
        don’t forget to multiply by 1000
        """
        if not settings:
            settings = self.msystem.get_settings()

        return settings.max_voltage * 1.2, settings.max_voltage / settings.internal_resistance * 1.2

    @abstractmethod
    def adjust_plot_borders(self, settings: Optional[MeasurementSettings] = None) -> Tuple[float, float]:
        """
        Adjust plot borders
        :param settings: 
        :return: 
        """
        raise NotImplementedError()

    def adjust_noise_amplitude(self, settings: Optional[MeasurementSettings] = None) -> Tuple[float, float]:
        """
        Get noise amplitude for specified settings
        :param settings: Measurement settings
        :return: v_amplitude, c_amplitude
        """
        if not settings:
            settings = self.msystem.get_settings()

        return settings.max_voltage / 20, settings.internal_resistance * 20


class EPLab(ProductBase):

    class Parameter(Enum):
        frequency = auto()
        voltage = auto()
        sensitive = auto()

    def __init__(self, msystem: MeasurementSystem):
        super(EPLab, self).__init__(msystem)

        self.mparams = {
            EPLab.Parameter.frequency:
                MeasurementParameter(EPLab.Parameter.frequency, "Частота пробного сигнала", "Probe signal frequency",
                                     [
                                         MeasurementParameterOption("10hz", (10, 1000), "10 Гц", "10 Hz"),
                                         MeasurementParameterOption("100hz", (100, 10000), "100 Гц", "100 Hz"),
                                         MeasurementParameterOption("1khz", (1000, 100000), "1 кГц", "1 kHz"),
                                         MeasurementParameterOption("10khz", (10000, 1000000), "10 кГц", "10 kHz"),
                                         MeasurementParameterOption("100khz", (100000, 2000000), "100 кГц", "100 kHz")
                                     ]),
            EPLab.Parameter.voltage:
                MeasurementParameter(EPLab.Parameter.voltage, "Амплитуда пробного сигнала", "Probe signal amplitude",
                                     [
                                         MeasurementParameterOption("1.2v", 1.2, "1.2 В", "1.2 V"),
                                         MeasurementParameterOption("3.3v", 3.3, "3.3 В", "3.3 V"),
                                         MeasurementParameterOption("5.0v", 5.0, "5.0 В", "5.0 V"),
                                         MeasurementParameterOption("12.0v", 12.0, "12.0 В", "12.0 V")
                                     ]),
            EPLab.Parameter.sensitive:
                MeasurementParameter(EPLab.Parameter.sensitive, "Чувствительность по току", "Current sensitive", [
                    MeasurementParameterOption("low", 475.0, "Низкая", "Low"),
                    MeasurementParameterOption("middle", 4750.0, "Средняя", "Middle"),
                    MeasurementParameterOption("high", 47500.0, "Высокая", "High")
                ])
        }

    def get_current_options(self) -> Dict[Enum, str]:
        settings = self.msystem.get_settings()

        options = {}

        for option in self.mparams[EPLab.Parameter.frequency].options:
            if option.value == (settings.probe_signal_frequency, settings.sampling_rate):
                options[EPLab.Parameter.frequency] = option.name
        if not options.get(EPLab.Parameter.frequency):
            warn(f"Unknown device frequency and sampling rate {settings.probe_signal_frequency} "
                 f"{settings.sampling_rate}")

        for option in self.mparams[EPLab.Parameter.sensitive].options:
            if np.isclose(option.value, settings.internal_resistance, atol=self._precision):
                options[EPLab.Parameter.sensitive] = option.name
        if not options.get(EPLab.Parameter.sensitive):
            warn(f"Unknown device internal resistance {settings.internal_resistance}")

        for option in self.mparams[EPLab.Parameter.voltage].options:
            if np.isclose(option.value, settings.max_voltage, atol=self._precision):
                options[EPLab.Parameter.voltage] = option.name
        if not options.get(EPLab.Parameter.voltage):
            warn(f"Unknown device max voltage {settings.max_voltage}")

        return options

    def set_settings_from_options(self, params: Dict[Enum, str]):
        settings = self.msystem.get_settings()
        if EPLab.Parameter.frequency in params:
            for option in self.mparams[EPLab.Parameter.frequency].options:
                if option.name == params[EPLab.Parameter.frequency]:
                    settings.probe_signal_frequency, settings.sampling_rate = option.value

        if EPLab.Parameter.voltage in params:
            for option in self.mparams[EPLab.Parameter.voltage].options:
                if option.name == params[EPLab.Parameter.voltage]:
                    settings.max_voltage = option.value

        if EPLab.Parameter.sensitive in params:
            for option in self.mparams[EPLab.Parameter.sensitive].options:
                if option.name == params[EPLab.Parameter.sensitive]:
                    settings.internal_resistance = option.value

        self.msystem.set_settings(settings)

    def adjust_plot_scale(self, settings: Optional[MeasurementSettings] = None) -> Tuple[float, float]:
        scale_adjuster = {  # _scale_adjuster[V][Omh] -> Scale for x,y
            (1.2, 47500.0): (1.5, 0.04),
            (1.2, 4750.0): (1.5, 0.4),
            (1.2, 475.0): (1.5, 4.0),
            (3.3, 47500.0): (4.0, 0.15),
            (3.3, 4750.0): (4.0, 1.0),
            (3.3, 475.0): (4.0, 10.0),
            (5.0, 47500.0): (6.0, 0.18),
            (5.0, 4750.0): (6.0, 1.5),
            (5.0, 475.0): (6.0, 15.0),
            (12.0, 47500.0): (14.0, 0.35),
            (12.0, 4750.0): (14.0, 2.8),
            (12.0, 475.0): (14.0, 28.0)
        }

        for key, value in scale_adjuster.items():
            if np.isclose(settings.max_voltage, key[0], atol=self._precision) and \
                    np.isclose(settings.internal_resistance, key[1], atol=self._precision):
                return value

        return super(EPLab, self).adjust_plot_scale(settings)

    def adjust_plot_borders(self, settings: Optional[MeasurementSettings] = None) -> Tuple[float, float]:
        """
        Adjust plot borders
        :param settings: MeasurementSettings
        :return: voltage, current border
        """
        if not settings:
            settings = self.msystem.get_settings()

        volt_border = 0

        volt_border_adjuster = {
            1.2: 0.4,
            3.3: 1.0,
            5.0: 1.5,
            12.0: 4.0
        }

        curr_border = 0

        curr_border_adjuster = {
            47500.0: 0.05,
            4750.0: 0.5,
            475: 5.0
        }

        for volt, border in volt_border_adjuster.items():
            if np.isclose(volt, settings.max_voltage, atol=self._precision):
                volt_border = border
                break
        for resist, border in curr_border_adjuster.items():
            if np.isclose(resist, settings.internal_resistance, atol=self._precision):
                curr_border = border

        return volt_border, curr_border

    def adjust_noise_amplitude(self, settings: Optional[MeasurementSettings] = None) -> Tuple[float, float]:
        """
        Get noise amplitude for specified settings
        :param settings: Measurement settings
        :return: v_amplitude, c_amplitude
        """
        if not settings:
            settings = self.msystem.get_settings()

        # max_voltage, internal_resistance -> v_amplitude, c_amplitude
        noise_adjuster = {
            (12.0, 475.0): (0.6, 0.008),
            (5.0, 475.0): (0.6, 0.008),
            (3.3, 475.0): (0.3, 0.008),
            (1.2, 475.0): (0.3, 0.008),
            (12.0, 4750.0): (0.6, 0.0005),
            (5.0, 4750.0): (0.3, 0.0005),
            (3.3, 4750.0): (0.3, 0.0005),
            (1.2, 4750.0): (0.3, 0.0005),
            (12.0, 47500.0): (0.6, 0.00005),
            (5.0, 47500.0): (0.3, 0.00005),
            (3.3, 47500.0): (0.3, 0.00005),
            (1.2, 47500.0): (0.3, 0.00005)
        }

        for key, value in noise_adjuster.items():
            if np.isclose(settings.max_voltage, key[0], atol=self._precision) and \
                    np.isclose(settings.internal_resistance, key[1], atol=self._precision):
                return value

        return super(EPLab, self).adjust_noise_amplitude(settings)
