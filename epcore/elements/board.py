from dataclasses import dataclass
from typing import List, Dict
from .element import Element
from .abstract import JsonConvertible


@dataclass
class Board(JsonConvertible):
    """
    Printed circuit board class.
    Normally board contain a number of components,
    which can be tested.
    """

    elements: List[Element]
    version: str

    def to_json(self) -> Dict:
        """
        Return object as dict with structure
        compatible with UFIV JSON file schema
        """

        json_data = {
            "elements": [el.to_json() for el in self.elements],
            "version": self.version
        }

        return json_data

    @classmethod
    def create_from_json(cls, json: Dict) -> "Board":
        """
        Create object from dict with structure
        compatible with UFIV JSON file schema
        """
        return Board(
            elements=[Element.create_from_json(el) for el in json["elements"]],
            version=json["version"]
        )
