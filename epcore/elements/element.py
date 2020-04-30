from typing import List, Optional, Dict
import logging
from .measurement import Measurement
from .pin import Pin


class Element:
    """
    Class for a PCB component.
    In most cases it has a number of pins
    which can be tested electrically
    """
    def __init__(self, pins: Optional[List[Pin]] = None):
        logging.debug("New element!")
        self.pins = pins

    def to_json_dict(self) -> Dict:
        """
        Return object as dict with structure
        compatible with UFIV JSON file schema
        """
        json_data = dict()
        json_data["pins"] = []
        for p in self.pins:
            json_data["pins"].append(p.to_json_dict())
        return json_data

    @classmethod
    def create_from_json_dict(cls, json_data: Dict) -> "Element":
        """
        Create object from dict with structure
        compatible with UFIV JSON file schema
        """
        pins = []
        for p in json_data["pins"]:
            pins.append(Pin.create_from_json_dict(p))
        return Element(
            pins=pins
        )
