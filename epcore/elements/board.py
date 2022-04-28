from dataclasses import dataclass, field
from typing import Dict, List, Optional
from warnings import warn
from PIL.Image import Image
from .abstract import JsonConvertible
from .element import Element

version = "1.1.2"


@dataclass
class PCBInfo(JsonConvertible):
    """
    Data related to the PCB (printed circuit board) and not the mounted components on the board.
    """

    pcb_name: Optional[str] = None
    image_resolution_ppcm: Optional[float] = None
    comment: Optional[str] = None

    @classmethod
    def create_from_json(cls, json_data: Dict) -> "PCBInfo":
        """
        Create object from dict with structure compatible with UFIV JSON file schema.
        :param json_data: dict with information.
        :return: object.
        """

        return PCBInfo(
            pcb_name=json_data.get("pcb_name"),
            image_resolution_ppcm=json_data.get("image_resolution_ppcm"),
            comment=json_data.get("comment")
        )

    def to_json(self) -> Dict:
        """
        Return dict with structure compatible with UFIV JSON file schema.
        :return: dict with information about object.
        """

        json_data = {"pcb_name": self.pcb_name,
                     "image_resolution_ppcm": self.image_resolution_ppcm,
                     "comment": self.comment}
        return self.remove_unused(json_data)


@dataclass
class Board(JsonConvertible):
    """
    Printed circuit board class. Normally board contains a number of components,
    which can be tested.
    """

    elements: List[Element] = field(default_factory=lambda: [])
    image: Optional[Image] = None
    pcb: Optional[PCBInfo] = None

    @classmethod
    def create_from_json(cls, json_data: Dict) -> "Board":
        """
        Create object from dict with structure compatible with UFIV JSON file schema.
        :param json_data: dict with information about board.
        :return: board object.
        """

        if json_data["version"] != version:
            warn(f"Module version {version} does not match version of file {json_data['version']}")
        return Board(
            elements=[Element.create_from_json(el) for el in json_data["elements"]],
            pcb=PCBInfo.create_from_json(json_data.get("PCB", {}))
        )

    def to_json(self) -> Dict:
        """
        Return dict with structure compatible with UFIV JSON file schema.
        :return: dict with information about board.
        """

        return {"elements": [el.to_json() for el in self.elements],
                "version": version}
