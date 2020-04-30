from typing import List, Optional, Dict
import logging
from .measurement import Measurement
from .pin import Pin
from .element import Element


class Board:
    """
    Printed circuit board class.
    Normally board contain a number of components,
    which can be tested.
    """
    def __init__(self, elements: Optional[List[Element]] = None):
        logging.debug("New board!")
        self.elements = elements or []

    def to_json_dict(self) -> Dict:
        """
        Return object as dict with structure
        compatible with UFIV JSON file schema
        """
        json_data = dict()
        json_data["elements"] = []
        for el in self.elements:
            json_data["elements"].append(el.to_json_dict())
        return json_data

    @classmethod
    def create_from_json_dict(cls, json_data: Dict) -> "Board":
        """
        Create object from dict with structure
        compatible with UFIV JSON file schema
        """
        elements = []
        for el in json_data["elements"]:
            elements.append(Element.create_from_json_dict(el))
        return Board(
            elements=elements
        )
