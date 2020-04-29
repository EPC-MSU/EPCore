from typing import List
import logging
from .measurement import Measurement

class Pin:
    """
    Class for a pin of electric component.
    """
    def __init__(self, measurements: List[Measurement] = [], comment: str = ""):
        logging.debug("New pin!")
        self.measurements = measurements
        self.comment = comment


    def to_json_dict(self) -> dict:
        """
        Return object as dict with structure
        compatible with UFIV JSON file schema
        """
        json_data = {}
        json_data["comment"] = self.comment
        json_data["ivc"] = []
        for m in self.measurements:
            json_data["ivc"].append(m.to_json_dict())
        return json_data

    @classmethod
    def create_from_json_dict(cls, json_data: dict) -> "Pin":
        """
        Create object from dict with structure
        compatible with UFIV JSON file schema
        """
        measurements = []
        for m in json_data["ivc"]:
            measurements.append(Measurement.create_from_json_dict(m))
        return Pin(
            comment=json_data["comment"],
            measurements=measurements
        )
