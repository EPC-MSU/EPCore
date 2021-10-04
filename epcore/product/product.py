import json
from abc import abstractmethod
from dataclasses import dataclass
from enum import auto, Enum
from os.path import abspath, dirname, join
from typing import Any, Dict, List, Optional, Tuple
from warnings import warn
import jsonschema
import numpy as np
from epcore.elements import MeasurementSettings


class InvalidJson(ValueError):
    pass


@dataclass
class MeasurementParameterOption:
    name: str
    value: Any
    label_ru: str
    label_en: str

    @classmethod
    def from_json(cls, json_data: Dict) -> "MeasurementParameterOption":
        return MeasurementParameterOption(name=json_data["name"],
                                          value=json_data["value"],
                                          label_ru=json_data["label_ru"],
                                          label_en=json_data["label_en"])


@dataclass
class MeasurementParameter:
    name: Enum
    options: List[MeasurementParameterOption]


@dataclass
class PlotParameters:
    ref_color: str
    test_color: str

    @classmethod
    def from_json(cls, json_data: Dict) -> "PlotParameters":
        return PlotParameters(json_data["ref_color"], json_data["test_color"])


class ProductBase:
    """
    This class defines the whole system functionality. If you want to add
    additional information, limitations or change behavior for some methods,
    simply derive an other class for your product from this base class.
    """

    _precision = 0.01

    def __init__(self):
        self.mparams = {}

    def get_all_available_options(self) -> Dict[Enum, MeasurementParameter]:
        """
        Get all parameters and all available options. If you have a state
        machine and from current state only subset of options is available,
        you should redefine this function and add additional logic here.
        """

        return self.mparams

    @abstractmethod
    def settings_to_options(self, settings: MeasurementSettings) -> Dict[Enum, str]:
        """
        Convert measurement settings to options set. If you want to add
        additional limitations for parameter combinations in your product,
        redefine this function.
        """

        raise NotImplementedError()

    @abstractmethod
    def options_to_settings(self, options: Dict[Enum, str],
                            settings: MeasurementSettings) -> MeasurementSettings:
        """
        Convert options set to measurement settings.
        """

        raise NotImplementedError()

    def adjust_plot_scale(self, settings: MeasurementSettings) -> Tuple[float, float]:
        """
        You can use this function for setting IVCurve plot scale for current
        setting. By default it returns:
        voltage = max_voltage * 1.2
        current = max_voltage * 1.2
        If you want to adjust the scale for some modes, you should redefine
        this function.
        Note! This function return value in A, but you probably will plot
        current in mA, don’t forget to multiply by 1000.
        """

        voltage_scale = 1.2 * settings.max_voltage
        current_scale = 1000 * 1.2 * settings.max_voltage / settings.internal_resistance
        return voltage_scale, current_scale

    @abstractmethod
    def adjust_plot_borders(self, settings: MeasurementSettings) -> Tuple[float, float]:
        """
        Adjust plot borders.
        """

        raise NotImplementedError()

    def adjust_noise_amplitude(self, settings: MeasurementSettings) -> Tuple[float, float]:
        """
        Get noise amplitude for specified settings.
        :param settings: measurement settings.
        :return: v_amplitude, c_amplitude.
        """

        return settings.max_voltage / 20, settings.internal_resistance * 20

    @property
    def plot_parameters(self) -> PlotParameters:
        """
        Get plot parameters.
        """

        return PlotParameters("#FF0000", "#0000FF")


@dataclass
class MeasurementParameterOptionEplab:
    """
    Class for object that contains full information about options of parameter
    of measuring system.
    """

    name: str
    value: Any
    label_ru: str
    label_en: str
    dependent_params: dict

    def _find_dependent_option(self, required_option_name: str, parameter: "Parameter") ->\
            Optional["MeasurementParameterOptionEplab"]:
        """
        Method returns option of dependent parameter with given names.
        :param required_option_name: name of required option;
        :param parameter: name of dependent parameter.
        :return: required option if it is found, first option of dependent
        parameter if required option is not found or None if there is not
        dependent parameter.
        """

        for option in self.dependent_params[parameter]:
            if required_option_name == option.name:
                return option
        if self.dependent_params[parameter]:
            return self.dependent_params[parameter][0]
        return None

    def _find_dependent_option_by_value(
            self, settings: MeasurementSettings, parameter: "Parameter") ->\
            Optional["MeasurementParameterOptionEplab"]:
        """
        Method returns option of dependent parameter with given values.
        :param settings: measurement settings;
        :param parameter: name of dependent parameter.
        :return: required option if it is found, otherwise None.
        """

        for option in self.dependent_params[parameter]:
            if parameter == EPLab.Parameter.frequency:
                if option.value == [settings.probe_signal_frequency, settings.sampling_rate]:
                    return option
            elif parameter == EPLab.Parameter.voltage:
                if option.value == settings.max_voltage:
                    return option
            elif parameter == EPLab.Parameter.sensitive:
                if option.value == settings.internal_resistance:
                    return option
        return None

    @classmethod
    def from_json(cls, json_data: Dict) -> "MeasurementParameterOptionEplab":
        """
        Method creates object from dictionary.
        :param json_data: dictionary with data about options of parameter.
        :return: object of class with full information about options of
        parameter.
        """

        parameters = {EPLab.Parameter.frequency: "frequency",
                      EPLab.Parameter.voltage: "voltage",
                      EPLab.Parameter.sensitive: "sensitive"}
        dependent_params = {}
        for parameter, parameter_name in parameters.items():
            if parameter_name in json_data.keys():
                dependent_params[parameter] = []
                for option in json_data[parameter_name]:
                    eplab_option = MeasurementParameterOptionEplab.from_json(option)
                    dependent_params[parameter].append(eplab_option)
        return MeasurementParameterOptionEplab(
            name=json_data["name"], value=json_data["value"], label_ru=json_data["label_ru"],
            label_en=json_data["label_en"], dependent_params=dependent_params)

    def get_available(self, settings: MeasurementSettings) -> Dict["Parameter", List]:
        """
        Method returns available options for dependent parameters of given
        option.
        :param settings: measurement settings.
        :return: dictionary with available options.
        """

        available = {}
        for dependent_param in self.dependent_params:
            new_available = {dependent_param: self.dependent_params[dependent_param]}
            available = {**available, **new_available}
            option = self._find_dependent_option_by_value(settings, dependent_param)
            new_available = option.get_available(settings)
            available = {**available, **new_available}
        return available

    def get_only_option(self) -> MeasurementParameterOption:
        """
        Method returns object of MeasurementParameterOption class with the same
        values of same attributes.
        :return: object of MeasurementParameterOption.
        """

        return MeasurementParameterOption(name=self.name, value=self.value, label_ru=self.label_ru,
                                          label_en=self.label_en)

    def set_option(self, options: Dict["Parameter", str], settings: MeasurementSettings,
                   parameter: "Parameter"):
        """
        Method writes value of parameter from
        :param options: dictionary with options of parameters;
        :param settings: measurement settings;
        :param parameter: parameter name.
        """

        options[parameter] = self.name
        for dependent_param in self.dependent_params:
            option = self._find_dependent_option_by_value(settings, dependent_param)
            option.set_option(options, settings, dependent_param)

    def write_to_settings(self, options: Dict["Parameter", str], settings: MeasurementSettings,
                          parameter: "Parameter"):
        """
        Method writes value of parameter from options dictionary to
        measurement settings.
        :param options: dictionary with string values of parameters;
        :param settings: measurement settings to write values to;
        :param parameter: name of parameter value of which should be written
        to settings.
        """

        if parameter == EPLab.Parameter.frequency:
            settings.probe_signal_frequency, settings.sampling_rate = self.value
        elif parameter == EPLab.Parameter.voltage:
            settings.max_voltage = self.value
        elif parameter == EPLab.Parameter.sensitive:
            settings.internal_resistance = self.value
        for dependent_param in self.dependent_params:
            option = self._find_dependent_option(options[dependent_param], dependent_param)
            option.write_to_settings(options, settings, dependent_param)


class Parameters:
    """
    Class for object that contains full information about parameters of
    measuring system.
    """

    _precision = 0.01

    def __init__(self, data: Dict = None, precision: float = None):
        """
        :param data: dictionary with parameters of measurement system;
        :param precision: accuracy for estimating the approximate equality
        of real numbers.
        """

        self.frequencies: List[MeasurementParameterOptionEplab] = []
        self.voltages: List[MeasurementParameterOptionEplab] = []
        self.sensitives: List[MeasurementParameterOptionEplab] = []
        if precision is not None:
            self._precision = precision
        if data is not None:
            self.initialize(data)

    @staticmethod
    def _check_dict_for_recording(options: Dict["Parameter", Any]) -> bool:
        """
        Method checks if options dictionary has all required fields.
        :param options: options dictionary.
        :return: True if options dictionary has all required fields.
        """

        if None in (options.get(EPLab.Parameter.frequency), options.get(EPLab.Parameter.voltage),
                    options.get(EPLab.Parameter.sensitive)):
            return False
        return True

    @staticmethod
    def _check_settings_for_recording(settings: MeasurementSettings) -> bool:
        """
        Method checks if settings values ​​include -1.
        :param settings: measurement settings.
        :return: True if settings values do not have -1 and were overwritten.
        """

        if -1 in (settings.probe_signal_frequency, settings.sampling_rate,
                  settings.max_voltage, settings.internal_resistance):
            return False
        return True

    @staticmethod
    def _create_measurement_parameter(data: List[Dict]) -> List[MeasurementParameterOptionEplab]:
        """
        Method returns list of options of measurement parameter.
        :param data: dictionary with data of parameter.
        :return: list of options of measurement parameter.
        """

        return [MeasurementParameterOptionEplab.from_json(option) for option in data]

    @staticmethod
    def _set_settings(settings_to: MeasurementSettings, settings_from: MeasurementSettings):
        """
        Method rites values ​​from one settings to another.
        :param settings_to: settings to write values ​​to;
        :param settings_from: settings to be read.
        """

        settings_to.probe_signal_frequency = settings_from.probe_signal_frequency
        settings_to.sampling_rate = settings_from.sampling_rate
        settings_to.max_voltage = settings_from.max_voltage
        settings_to.internal_resistance = settings_from.internal_resistance

    def get_available_options(self, settings: MeasurementSettings) -> Dict["Parameter", List]:
        """
        Method returns available options for parameters of measuring system.
        :param settings: measurement settings.
        :return: dictionary with available options for parameters.
        """

        available = {EPLab.Parameter.frequency: self.frequencies}
        for option in self.frequencies:
            if option.value == [settings.probe_signal_frequency, settings.sampling_rate]:
                new_available = option.get_available(settings)
                available = {**available, **new_available}
                break
        if self._check_dict_for_recording(available):
            return available
        available[EPLab.Parameter.voltage] = self.voltages
        for option in self.voltages:
            if option.value == settings.max_voltage:
                new_available = option.get_available(settings)
                available = {**available, **new_available}
        if self._check_dict_for_recording(available):
            return available
        available[EPLab.Parameter.sensitive] = self.sensitives
        for option in self.sensitives:
            if option.value == settings.internal_resistance:
                new_available = option.get_available(settings)
                available = {**available, **new_available}
        return available

    def get_options(self, settings: MeasurementSettings) -> Dict["Parameter", str]:
        """
        Method writes values from measurement settings to dictionary with
        options of parameters.
        :param settings: measurement settings.
        :return: dictionary with options of parameters.
        """

        options = {}
        for option in self.frequencies:
            if option.value == [settings.probe_signal_frequency, settings.sampling_rate]:
                option.set_option(options, settings, EPLab.Parameter.frequency)
                break
        if self._check_dict_for_recording(options):
            return options
        if not options.get(EPLab.Parameter.frequency):
            warn(f"Unknown device frequency and sampling rate {settings.probe_signal_frequency} "
                 f"{settings.sampling_rate}")
        for option in self.voltages:
            if np.isclose(option.value, settings.max_voltage, atol=self._precision):
                option.set_option(options, settings, EPLab.Parameter.voltage)
                break
        if self._check_dict_for_recording(options):
            return options
        if not options.get(EPLab.Parameter.voltage):
            warn(f"Unknown device max voltage {settings.max_voltage}")
        for option in self.sensitives:
            if np.isclose(option.value, settings.internal_resistance, atol=self._precision):
                option.set_option(options, settings, EPLab.Parameter.sensitive)
                break
        if not options.get(EPLab.Parameter.sensitive):
            warn(f"Unknown device internal resistance {settings.internal_resistance}")
        return options

    def get_parameters(self) -> Dict["Parameter", MeasurementParameter]:
        """
        Method returns dictionary with measurement parameters of measuring
        system. This method works correctly if EPLab uses default json-file
        with options.
        :return: dictionary with measurement parameters.
        """

        result = {}
        parameters = self.frequencies, self.voltages, self.sensitives
        names = EPLab.Parameter.frequency, EPLab.Parameter.voltage, EPLab.Parameter.sensitive
        for i_parameter, parameter in enumerate(parameters):
            options = [item.get_only_option() for item in parameter]
            param_name = names[i_parameter]
            result[param_name] = MeasurementParameter(param_name, options)
        return result

    def initialize(self, data: Dict):
        """
        Method reads dictionary with data from json-file that contains options
        for measuring system.
        :param data: dictionary with parameters of measurement system.
        """

        frequencies_data = data.get("frequency")
        if frequencies_data:
            self.frequencies = self._create_measurement_parameter(frequencies_data)
        voltages_data = data.get("voltage")
        if voltages_data:
            self.voltages = self._create_measurement_parameter(voltages_data)
        sensitives_data = data.get("sensitive")
        if sensitives_data:
            self.sensitives = self._create_measurement_parameter(sensitives_data)

    def write_to_settings(self, options: Dict["Parameter", str], settings: MeasurementSettings):
        """
        Method writes values from options dictionary to measurement settings.
        :param options: dictionary with string values of parameters;
        :param settings: measurement settings to write values to.
        :return: measurement settings with recorded values.
        """

        new_settings = MeasurementSettings(-1, -1, -1, -1)
        for option in self.frequencies:
            if option.name == options[EPLab.Parameter.frequency]:
                option.write_to_settings(options, new_settings, EPLab.Parameter.frequency)
                break
        if self._check_settings_for_recording(new_settings):
            self._set_settings(settings, new_settings)
            return
        for option in self.voltages:
            if option.name == options[EPLab.Parameter.voltage]:
                option.write_to_settings(options, new_settings, EPLab.Parameter.voltage)
                break
        if self._check_settings_for_recording(new_settings):
            self._set_settings(settings, new_settings)
            return
        for option in self.sensitives:
            if option.name == options[EPLab.Parameter.sensitive]:
                option.write_to_settings(options, new_settings, EPLab.Parameter.sensitive)
                break
        self._set_settings(settings, new_settings)


class EPLab(ProductBase):

    class Parameter(Enum):
        frequency = auto()
        voltage = auto()
        sensitive = auto()

    @classmethod
    def _open_json(cls, json_filename: str) -> Dict:
        """
        Method opens json file with options.
        :param json_filename: name of json file.
        :return: data from json file.
        """

        with open(join(dirname(abspath(__file__)), json_filename), "r",
                  encoding="utf-8") as file:
            return json.load(file)

    @classmethod
    def _schema(cls) -> Dict:
        with open(join(dirname(abspath(__file__)), "doc", "eplab_schema.json"), "r",
                  encoding="utf-8") as file:
            return json.load(file)

    def __init__(self, json_data: Optional[Dict] = None):
        """
        :param json_data: dictionary with options for parameters of measurement
        system.
        """

        super().__init__()
        self.change_options(json_data)

    def change_options(self, json_data: Optional[Dict] = None):
        """
        Method changes options for parameters of measurement system.
        :param json_data: dictionary with options for parameters of measurement
        system.
        """

        if json_data is None:
            json_data = EPLab._open_json("eplab_default_options.json")
        try:
            jsonschema.validate(json_data, EPLab._schema())
        except jsonschema.ValidationError as err:
            raise InvalidJson("Validation error: " + str(err)) from err
        json_options = json_data["options"]
        self._plot_parameters = PlotParameters.from_json(json_data["plot_parameters"])
        self._parameters = Parameters(json_options)

    @property
    def plot_parameters(self) -> PlotParameters:
        return self._plot_parameters

    def settings_to_options(self, settings: MeasurementSettings) -> Dict["Parameter", str]:
        """
        Method writes values from measurement settings to dictionary with
        options of parameters.
        :param settings: measurement settings.
        :return: dictionary with options.
        """

        return self._parameters.get_options(settings)

    def options_to_settings(self, options: Dict["Parameter", str],
                            settings: MeasurementSettings) -> MeasurementSettings:
        """
        Method writes values from options dictionary to measurement settings.
        :param options: dictionary with string values of parameters;
        :param settings: measurement settings to write values to.
        :return: measurement settings with recorded values.
        """

        self._parameters.write_to_settings(options, settings)
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
            (12.0, 475.0): (14.0, 28.0)}
        for key, value in scale_adjuster.items():
            if np.isclose(settings.max_voltage, key[0], atol=self._precision) and \
                    np.isclose(settings.internal_resistance, key[1], atol=self._precision):
                return value
        return super().adjust_plot_scale(settings)

    def adjust_plot_borders(self, settings: MeasurementSettings) -> Tuple[float, float]:
        """
        Adjust plot borders.
        :param settings: measurement settings.
        :return: voltage, current border.
        """

        volt_border = 0
        volt_border_adjuster = {1.2: 0.4,
                                3.3: 1.0,
                                5.0: 1.5,
                                12.0: 4.0}
        curr_border = 0
        curr_border_adjuster = {47500.0: 0.05,
                                4750.0: 0.5,
                                475: 5.0}
        for volt, border in volt_border_adjuster.items():
            if np.isclose(volt, settings.max_voltage, atol=self._precision):
                volt_border = border
                break
        for resist, border in curr_border_adjuster.items():
            if np.isclose(resist, settings.internal_resistance, atol=self._precision):
                curr_border = border
                break
        return volt_border, curr_border

    def adjust_noise_amplitude(self, settings: MeasurementSettings) -> Tuple[float, float]:
        """
        Get noise amplitude for specified settings.
        :param settings: measurement settings.
        :return: v_amplitude, c_amplitude.
        """

        # max_voltage, internal_resistance -> v_amplitude, c_amplitude
        noise_adjuster = {(12.0, 475.0): (0.6, 0.008),
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
                          (1.2, 47500.0): (0.3, 0.00005)}
        for key, value in noise_adjuster.items():
            if np.isclose(settings.max_voltage, key[0], atol=self._precision) and \
                    np.isclose(settings.internal_resistance, key[1], atol=self._precision):
                return value
        return super().adjust_noise_amplitude(settings)

    def get_available_options(self, settings: MeasurementSettings) -> Dict["Parameter", List]:
        """
        Method returns available options for parameters of measuring system.
        :param settings: measurement settings.
        :return: dictionary with available options for parameters.
        """

        return self._parameters.get_available_options(settings)

    def get_parameters(self) -> Dict:
        """
        Method returns dictionary with options of parameters of measuring
        system. This method works correctly if EPLab uses default json-file
        with options.
        :return: dictionary with options of parameters.
        """

        return self._parameters.get_parameters()
