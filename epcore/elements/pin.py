from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from .abstract import JsonConvertible
from .measurement import Measurement, MeasurementSettings


@dataclass
class MultiplexerOutput(JsonConvertible):
    """
    Class for information about multiplexer output.
    """

    channel_number: int = None
    module_number: int = None

    @classmethod
    def create_from_json(cls, json_dict: Dict[str, Any]) -> Optional["MultiplexerOutput"]:
        """
        Create object from dict with structure compatible with UFIV JSON file schema.
        :param json_dict: dict with information.
        :return: object.
        """

        if json_dict.get("channel_number") and json_dict.get("module_number"):
            return MultiplexerOutput(channel_number=json_dict.get("channel_number"),
                                     module_number=json_dict.get("module_number"))
        return None

    def to_json(self) -> Dict[str, Any]:
        """
        Return dict with structure compatible with UFIV JSON file schema.
        :return: dict with information about object.
        """

        json_dict = {"channel_number": self.channel_number,
                     "module_number": self.module_number}
        return self.remove_unused(json_dict)


@dataclass
class Pin(JsonConvertible):
    """
    Class for a pin of electric component.
    """

    x: float
    y: float
    comment: Optional[str] = None
    measurements: Optional[List[Measurement]] = field(default_factory=list)
    multiplexer_output: Optional[MultiplexerOutput] = None

    def append_test_measurement(self, measurement: Measurement) -> None:
        """
        Append new test measurement to pin.
        :param measurement: new test measurement.
        """

        if measurement.is_reference:
            raise ValueError("It must be non reference measurement")
        self.measurements.append(measurement)

    @classmethod
    def create_from_json(cls, json_data: Dict[str, Any]) -> "Pin":
        """
        Create object from dict with structure compatible with UFIV JSON file schema.
        :param json_data: dict with information.
        :return: pin object.
        """

        return Pin(
            comment=json_data.get("comment"),
            x=json_data["x"],
            y=json_data["y"],
            measurements=[Measurement.create_from_json(measure) for measure in json_data["iv_curves"]],
            multiplexer_output=MultiplexerOutput.create_from_json(json_data.get("multiplexer_output", {}))
        )

    def get_main_measurement(self) -> Optional[Measurement]:
        """
        :return: first non reference measurement.
        """

        non_ref = self.get_non_reference_measurements()
        return None if len(non_ref) == 0 else non_ref[0]

    def get_non_reference_measurements(self) -> Optional[List[Measurement]]:
        """
        :return: list of non reference measurements.
        """

        return [measurement for measurement in self.measurements if not measurement.is_reference]

    def get_reference_and_test_measurements(self) -> Tuple[Optional[Measurement], Optional[Measurement],
                                                           Optional[MeasurementSettings]]:
        """
        Method looks for reference measurement and test measurement with the same settings.
        :return: tuple with reference measurement, test measurement and their settings.
        """

        ref_measurement = self.get_reference_measurement()
        if ref_measurement:
            settings = ref_measurement.settings
        else:
            settings = None
        for measurement in self.measurements:
            if not measurement.is_reference and ((settings and measurement.settings == settings) or not settings):
                return ref_measurement, measurement, measurement.settings
        return ref_measurement, None, settings

    def get_reference_measurement(self) -> Optional[Measurement]:
        """
        :return: reference measurement.
        """

        reference_measures = [measurement for measurement in self.measurements if measurement.is_reference]
        if not reference_measures:
            return None
        if len(reference_measures) > 2:
            raise ValueError("Too many reference curves; can't choose")
        return reference_measures[0]

    def set_test_measurement(self, measurement: Measurement) -> None:
        """
        Set new test measurement to pin.
        :param measurement: new test measurement.
        """

        if measurement.is_reference:
            raise ValueError("It must be test measurement")
        self.measurements = [m for m in self.measurements if m.is_reference]
        self.measurements.append(measurement)

    def set_reference_measurement(self, measurement: Measurement, invalidate_test: bool = False) -> None:
        """
        Set new reference measurement to pin.
        :param measurement: new reference measurement;
        :param invalidate_test: if True then test measurements will be removed from pin.
        """

        if not measurement.is_reference:
            raise ValueError("It must be reference measurement")
        if invalidate_test:
            self.measurements = [measurement]
        else:
            self.measurements = [m for m in self.measurements if not m.is_reference]
            self.measurements.append(measurement)

    def to_json(self) -> Dict[str, Any]:
        """
        Return dict with structure compatible with UFIV JSON file schema.
        :return: dict with information about pin object.
        """

        json_data = {
            "comment": self.comment,
            "x": self.x,
            "y": self.y,
            "iv_curves": [measure.to_json() for measure in self.measurements]
        }
        if self.multiplexer_output and self.multiplexer_output.to_json():
            json_data["multiplexer_output"] = self.multiplexer_output.to_json()
        return self.remove_unused(json_data)
