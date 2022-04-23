from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .abstract import JsonConvertible
from .measurement import Measurement


@dataclass
class MultiplexerOutput(JsonConvertible):
    """
    Class for information about multiplexer output.
    """

    channel_number: int = None
    module_number: int = None

    @classmethod
    def create_from_json(cls, json_dict: Dict) -> Optional["MultiplexerOutput"]:
        """
        Create object from dict with structure compatible with UFIV JSON file schema.
        :param json_dict: dict with information.
        :return: object.
        """

        if json_dict.get("channel_number") and json_dict.get("module_number"):
            return MultiplexerOutput(channel_number=json_dict.get("channel_number"),
                                     module_number=json_dict.get("module_number"))
        return None

    def to_json(self) -> Dict:
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

    @classmethod
    def create_from_json(cls, json_data: Dict) -> "Pin":
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
        non_ref = self.get_non_reference_measurements()
        return None if len(non_ref) == 0 else non_ref[0]

    def get_non_reference_measurements(self) -> Optional[List[Measurement]]:
        return [m for m in self.measurements if not m.is_reference]

    def get_reference_measurement(self) -> Optional[Measurement]:
        reference_measures = [m for m in self.measurements if m.is_reference]
        if not reference_measures:
            return None
        if len(reference_measures) > 2:
            raise ValueError("Too many reference curves; can't choose")
        return reference_measures[0]

    def set_reference_measurement(self, measurement: Measurement):
        # First, remove all reference measurements
        self.measurements = [m for m in self.measurements if not m.is_reference]
        if not measurement.is_reference:
            raise ValueError("It must be reference measurement")
        # Add reference measurement
        self.measurements.append(measurement)

    def to_json(self) -> Dict:
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
        return self.remove_unused(json_data)
