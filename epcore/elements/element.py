from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from .abstract import JsonConvertible
from .pin import Pin


@dataclass
class Element(JsonConvertible):
    """
    Class for a PCB component.
    In most cases it has a number of pins
    which can be tested electrically
    """

    pins: List[Pin]
    name: Optional[str] = None
    package: Optional[str] = None
    center: Optional[Tuple[float, float]] = None
    bounding_zone: Optional[List[Tuple[float, float]]] = None
    rotation: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None

    def to_json(self) -> Dict:
        """
        Return object as dict with structure
        compatible with UFIV JSON file schema
        """

        json_data = {
            "name": self.name,
            "pins": [pin.to_json() for pin in self.pins],
            "package": self.package,
            "center": self.center,
            "bounding_zone": self.bounding_zone,
            "rotation": self.rotation,
            "width": self.width,
            "height": self.height
        }

        return self.remove_unused(json_data)

    @classmethod
    def create_from_json(cls, json_data: Dict) -> "Element":
        """
        Create object from dict with structure
        compatible with UFIV JSON file schema
        """
        return Element(
            pins=[Pin.create_from_json(pin) for pin in json_data["pins"]],
            name=json_data.get("name"),
            package=json_data.get("package"),
            center=json_data.get("center"),
            bounding_zone=json_data.get("bounding_zone"),
            rotation=json_data.get("rotation"),
            width=json_data.get("width"),
            height=json_data.get("height")
        )