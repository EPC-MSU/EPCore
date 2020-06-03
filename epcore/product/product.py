from dataclasses import dataclass
from typing import List, Dict
from ..measurementmanager import MeasurementSystem


@dataclass
class MeasurementParameterOption():
    value: any
    label_ru: str
    label_en: str


@dataclass
class MeasurementParameter():
    options: List[MeasurementParameterOption]


@dataclass
class ProductBase:
    """
    This class defines the whole system functionality.
    If you want to add additional information, limitations or
    change behavior for some methods, simply derive an other class
    for your product from this base class.
    """
    def __init__(self):
        self.msystem = MeasurementSystem()
        self.mparams = {}
        # There will be something like:
        # {"probe_signal_frequency": MeasurementParameter(
        #    options = [
        #       MeasurementParameterOption(),
        #       MeasurementParameterOption(),
        #       MeasurementParameterOption()
        # ])}

    @classmethod
    def create_from_json(cls, json: Dict) -> "ProductBase":
        return ProductBase()

    def get_current_options(self) -> Dict[str, MeasurementParameterOption]:
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
        return {}

    def get_all_available_options(self) -> Dict[str, MeasurementParameter]:
        """
        This function returns all parameters and all available options.
        If you have a state machine and from current state
        only subset of options is available,
        you should redefine this function and add additional logic here.
        """
        return self.mparams

    def set_settings_from_options(self, mparams: Dict[str, MeasurementParameterOption]):
        """
        This function accepts dict of options and set settings to measurement system.
        In case there is no options for some parameters, they should keep their old value.
        So if you call set_settings_from_options({"probe_signal_frequency": (...)}),
        it means that probe signal frequency should be changed while
        voltage and internal resistance should stay unchanged.
        If you want to add additional limitations for parameter combinations in your product,
        redefine this function.
        """
        pass

    def get_curve_box_size() -> Dict[str, float]:
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
        return {"voltage": 3.3, "current": 0.025}
