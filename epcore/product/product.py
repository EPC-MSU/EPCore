from dataclasses import dataclass
from abc import abstractmethod
from typing import List, Dict, Any, Tuple, Optional
from epcore.elements import MeasurementSettings
from warnings import warn
from os.path import join, dirname
import numpy as np
import jsonschema
import json
from enum import Enum, auto


class InvalidJson(ValueError):
    pass


@dataclass
class MeasurementParameterOption:
    name: str
    value: Any
    label_ru: str
    label_en: str

    @classmethod
    def from_json(cls, json: Dict) -> "MeasurementParameterOption":
        return MeasurementParameterOption(name=json["name"],
                                          value=json["value"],
                                          label_ru=json["label_ru"],
                                          label_en=json["label_en"])


@dataclass
class MeasurementParameter:
    name: Enum
    options: List[MeasurementParameterOption]


@dataclass
class PlotParameters:
    ref_color: str
    test_color: str

    @classmethod
    def from_json(cls, json: Dict) -> "PlotParameters":
        return PlotParameters(json["ref_color"], json["test_color"])


class ProductBase:
    """
    This class defines the whole system functionality.
    If you want to add additional information, limitations or
    change behavior for some methods, simply derive an other class
    for your product from this base class.
    """
    _precision = 0.01

    def __init__(self):
        self.mparams = {}

    def get_all_available_options(self) -> Dict[Enum, MeasurementParameter]:
        """
        Get all parameters and all available options.
        If you have a state machine and from current state
        only subset of options is available,
        you should redefine this function and add additional logic here.
        """
        return self.mparams

    @abstractmethod
    def settings_to_options(self, settings: MeasurementSettings) -> Dict[Enum, str]:
        """
        Convert measurement settings to options set
        If you want to add additional limitations for parameter combinations in your product,
        redefine this function.
        """
        raise NotImplementedError()

    @abstractmethod
    def options_to_settings(self, options: Dict[Enum, str],
                            settings: MeasurementSettings) -> MeasurementSettings:
        """
        Convert options set to measurement settings
        """
        raise NotImplementedError()

    def adjust_plot_scale(self, settings: MeasurementSettings) -> Tuple[float, float]:
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

        return settings.max_voltage * 1.2, settings.max_voltage / settings.internal_resistance * 1.2

    @abstractmethod
    def adjust_plot_borders(self, settings: MeasurementSettings) -> Tuple[float, float]:
        """
        Adjust plot borders
        :param settings:
        :return:
        """
        raise NotImplementedError()

    def adjust_noise_amplitude(self, settings: MeasurementSettings) -> Tuple[float, float]:
        """
        Get noise amplitude for specified settings
        :param settings: Measurement settings
        :return: v_amplitude, c_amplitude
        """

        return settings.max_voltage / 20, settings.internal_resistance * 20

    @property
    def plot_parameters(self) -> PlotParameters:
        """
        Get plot parameters
        """
        return PlotParameters("#FF0000", "#0000FF")


class EPLab(ProductBase):

    class Parameter(Enum):
        frequency = auto()
        voltage = auto()
        sensitive = auto()

    @classmethod
    def _default_json(cls) -> Dict:
        with open(join(dirname(__file__), "eplab_default_options.json"), "r", encoding="utf-8") as file:
            return json.load(file)

    @classmethod
    def _schema(cls) -> Dict:
        with open(join(dirname(__file__), "doc", "eplab_schema.json"), "r") as file:
            return json.load(file)

    def __init__(self, json: Optional[Dict] = None):
        super(EPLab, self).__init__()

        if json is None:
            json = EPLab._default_json()

        try:
            jsonschema.validate(json, EPLab._schema())
        except jsonschema.ValidationError as err:
            raise InvalidJson("Validation error: " + str(err))

        json_options = json["options"]
        self._plot_parameters = PlotParameters.from_json(json["plot_parameters"])

        self.mparams = {
            EPLab.Parameter.frequency:
                MeasurementParameter(EPLab.Parameter.frequency,
                                     [MeasurementParameterOption.from_json(x) for x in json_options["frequency"]]),
            EPLab.Parameter.voltage:
                MeasurementParameter(EPLab.Parameter.voltage,
                                     [MeasurementParameterOption.from_json(x) for x in json_options["voltage"]]),
            EPLab.Parameter.sensitive:
                MeasurementParameter(EPLab.Parameter.sensitive,
                                     [MeasurementParameterOption.from_json(x) for x in json_options["sensitive"]])
        }

    @property
    def plot_parameters(self) -> PlotParameters:
        return self._plot_parameters

    def settings_to_options(self, settings: MeasurementSettings) -> Dict["Parameter", str]:
        options = {}

        for option in self.mparams[EPLab.Parameter.frequency].options:
            if option.value == [settings.probe_signal_frequency, settings.sampling_rate]:
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

    def options_to_settings(self, options: Dict["Parameter", str],
                            settings: MeasurementSettings) -> MeasurementSettings:

        if EPLab.Parameter.frequency in options:
            for option in self.mparams[EPLab.Parameter.frequency].options:
                if option.name == options[EPLab.Parameter.frequency]:
                    settings.probe_signal_frequency, settings.sampling_rate = option.value

        if EPLab.Parameter.voltage in options:
            for option in self.mparams[EPLab.Parameter.voltage].options:
                if option.name == options[EPLab.Parameter.voltage]:
                    settings.max_voltage = option.value

        if EPLab.Parameter.sensitive in options:
            for option in self.mparams[EPLab.Parameter.sensitive].options:
                if option.name == options[EPLab.Parameter.sensitive]:
                    settings.internal_resistance = option.value

        return settings

    def adjust_plot_scale(self, settings: MeasurementSettings) -> Tuple[float, float]:

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

    def adjust_plot_borders(self, settings: MeasurementSettings) -> Tuple[float, float]:
        """
        Adjust plot borders
        :param settings: MeasurementSettings
        :return: voltage, current border
        """

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

    def adjust_noise_amplitude(self, settings: MeasurementSettings) -> Tuple[float, float]:
        """
        Get noise amplitude for specified settings
        :param settings: Measurement settings
        :return: v_amplitude, c_amplitude
        """

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
