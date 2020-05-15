from dataclasses import dataclass
from typing import List, Dict, Optional
from .measurement import Measurement
from .abstract import JsonConvertible


@dataclass
class Pin(JsonConvertible):
    """
    Class for a pin of electric component.
    """

    x: float
    y: float
    measurements: List[Measurement]
    comment: Optional[str] = None

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
        Return object as dict with structure
        compatible with UFIV JSON file schema
        """

        json_data = {
            "comment": self.comment,
            "x": self.x,
            "y": self.y,
            "iv_curves": [measure.to_json() for measure in self.measurements]
        }

        return self.remove_unused(json_data)

    @classmethod
    def create_from_json(cls, json_data: Dict) -> "Pin":
        """
        Create object from dict with structure
        compatible with UFIV JSON file schema
        """
        return Pin(
            comment=json_data.get("comment"),
            x=json_data["x"],
            y=json_data["y"],
            measurements=[Measurement.create_from_json(measure) for measure in json_data["iv_curves"]]
        )
