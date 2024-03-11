import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
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
    def create_from_json(cls, json_data: Dict[str, Any]) -> "PCBInfo":
        """
        Create object from dict with structure compatible with UFIV JSON file schema.
        :param json_data: dictionary with information.
        :return: object.
        """

        return PCBInfo(
            pcb_name=json_data.get("pcb_name"),
            image_resolution_ppcm=json_data.get("image_resolution_ppcm"),
            comment=json_data.get("comment")
        )

    def to_json(self) -> Dict[str, Union[float, str]]:
        """
        :return: dictionary with information about object with structure compatible with UFIV JSON file schema.
        """

        json_data = {"pcb_name": self.pcb_name,
                     "image_resolution_ppcm": self.image_resolution_ppcm,
                     "comment": self.comment}
        return self.remove_unused(json_data)


@dataclass
class Board(JsonConvertible):
    """
    Printed circuit board class. Normally board contains a number of components, which can be tested.
    """

    elements: List[Element] = field(default_factory=lambda: [])
    image: Optional[Image] = None
    pcb: Optional[PCBInfo] = None

    @classmethod
    def create_from_json(cls, json_data: Dict[str, Any]) -> "Board":
        """
        Create object from dictionary with structure compatible with UFIV JSON file schema.
        :param json_data: dictionary with information about board.
        :return: board object.
        """

        if json_data["version"] != version:
            warn(f"Module version {version} does not match version of file {json_data['version']}")
        return Board(
            elements=[Element.create_from_json(element) for element in json_data["elements"]],
            pcb=PCBInfo.create_from_json(json_data.get("PCB", {}))
        )

    def to_json(self, save_image_if_needed_to: Optional[str] = None, board_path: Optional[str] = None
                ) -> Dict[str, Any]:
        """
        WARNING! When saving the board image, the programmer himself must maintain the relevance of the relative path
        to the image saved in json (see #91931).
        :param save_image_if_needed_to: folder where to save the image, if the board has an image;
        :param board_path: path to the file where the board is saved.
        :return: dictionary with information about board with structure compatible with UFIV JSON file schema.
        """

        pcb_info = self.pcb.to_json() if self.pcb is not None else dict()
        if save_image_if_needed_to and board_path and self.image:
            os.makedirs(save_image_if_needed_to, exist_ok=True)
            image_name = os.path.basename(board_path).replace(".uzf", ".png")
            image_path = os.path.join(save_image_if_needed_to, image_name)
            self.image.save(image_path)
            pcb_info["pcb_image_path"] = os.path.relpath(image_path, os.path.dirname(board_path))

        data = {"elements": [element.to_json() for element in self.elements],
                "version": version}
        if pcb_info:
            data["PCB"] = pcb_info
        return data
