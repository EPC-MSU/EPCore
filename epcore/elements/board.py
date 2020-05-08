from dataclasses import dataclass, field
from typing import List, Dict, Optional
from warnings import warn
from PyQt5.QtGui import QImage
from .element import Element
from .abstract import JsonConvertible

version = "1.1.0"


@dataclass
class Board(JsonConvertible):
    """
    Printed circuit board class.
    Normally board contain a number of components,
    which can be tested.
    """

    elements: List[Element] = field(default_factory=lambda: [])
    image: Optional[QImage] = None

    def to_json(self) -> Dict:
        """
        Return object as dict with structure
        compatible with UFIV JSON file schema
        """

        json_data = {
            "elements": [el.to_json() for el in self.elements],
            "version": version
        }

        return json_data

    @classmethod
    def create_from_json(cls, json: Dict) -> "Board":
        """
        Create object from dict with structure
        compatible with UFIV JSON file schema
        """
        if json["version"] != version:
            warn(f"Module version {version} does not match version of file {json['version']}")
        return Board(
            elements=[Element.create_from_json(el) for el in json["elements"]]
        )
