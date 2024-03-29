from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from .abstract import JsonConvertible
from .pin import Pin


@dataclass
class Element(JsonConvertible):
    """
    Class for a PCB component. In most cases it has a number of pins which can be tested electrically.
    """

    pins: List[Pin]
    name: Optional[str] = None
    package: Optional[str] = None
    # center: Optional[Tuple[float, float]] = None
    bounding_zone: Optional[List[Tuple[float, float]]] = field(default_factory=list)
    rotation: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    set_automatically: Optional[bool] = None

    @property
    def center(self) -> Optional[np.array]:
        """
        Return center of element.
        :return: center of element.
        """

        if self.bounding_zone is not None:
            if len(self.bounding_zone) > 0:
                return np.mean(np.array(self.bounding_zone), axis=0).tolist()
        if len(self.pins) > 0:
            arr_xy = [(pin.x, pin.y) for pin in self.pins]
            return np.mean(np.array(arr_xy), axis=0).tolist()
        return None

    @classmethod
    def create_from_json(cls, json_data: Dict[str, Any]) -> "Element":
        """
        Create object from dict with structure compatible with UFIV JSON file schema.
        :param json_data: dict with information about element.
        :return: element object.
        """

        return Element(
            pins=[Pin.create_from_json(pin) for pin in json_data["pins"]],
            set_automatically=json_data.get("set_automatically"),
            name=json_data.get("name"),
            package=json_data.get("package"),
            # center=json_data.get("center"),
            bounding_zone=json_data.get("bounding_zone"),
            rotation=json_data.get("rotation"),
            width=json_data.get("width"),
            height=json_data.get("height")
        )

    def to_json(self) -> Dict[str, Any]:
        """
        Return dict with structure compatible with UFIV JSON file schema.
        :return: dict with information about element.
        """

        json_data = {
            "name": self.name,
            "set_automatically": self.set_automatically,
            "pins": [pin.to_json() for pin in self.pins],
            "package": self.package,
            # "center": self.center,
            "bounding_zone": tuple(tuple(map(float, p)) for p in self.bounding_zone) if self.bounding_zone is not None
            else None,  # "is not None", yep, it's necessary
            "rotation": self.rotation,
            "width": self.width,
            "height": self.height
        }
        return self.remove_unused(json_data)
