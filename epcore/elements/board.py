import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from warnings import warn
from PIL import Image, ImageOps
from .abstract import JsonConvertible
from .element import Element
from .pcbinfo import PCBInfo


version = "1.1.2"


class ImageNotFoundError(FileNotFoundError):
    pass


@dataclass
class Board(JsonConvertible):
    """
    Printed circuit board class. Normally board contains a number of components, which can be tested.
    """

    elements: List[Element] = field(default_factory=lambda: [])
    image: Optional[Image.Image] = None
    pcb: Optional[PCBInfo] = None

    @classmethod
    def create_from_json(cls, json_data: Dict[str, Any], ignore_absent_image: bool = False,
                         board_path: Optional[str] = None) -> "Board":
        """
        Create object from dictionary with structure compatible with UFIV JSON file schema.
        :param json_data: dictionary with information about board;
        :param ignore_absent_image: if this flag is True, then in the absence of board image, we do not throw an
        exception and create board object without an image;
        :param board_path: path to the json file with the board.
        :return: board object.
        """

        if json_data["version"] != version:
            warn(f"Module version {version} does not match version of file {json_data['version']}")

        pcb_info = json_data.get("PCB", {})
        board = Board(elements=[Element.create_from_json(element) for element in json_data["elements"]],
                      pcb=PCBInfo.create_from_json(pcb_info))

        rel_image_path = pcb_info.get("pcb_image_path", None)
        if rel_image_path:
            if board_path is not None:
                image_path = os.path.join(os.path.dirname(board_path), rel_image_path)
            else:
                image_path = rel_image_path
            if os.path.isfile(image_path):
                image = ImageOps.exif_transpose(Image.open(image_path))
                board.image = image
            elif image_path and not ignore_absent_image and not os.path.isfile(image_path):
                raise ImageNotFoundError(f"No board image file '{image_path}'")

        return board

    def to_json(self, save_image_if_needed_to: Optional[str] = None, board_path: Optional[str] = None
                ) -> Dict[str, Any]:
        """
        WARNING! When saving the board image, the programmer himself must maintain the relevance of the relative path
        to the image saved in json (see #91931).
        :param save_image_if_needed_to: path where to save the image, if the board has an image;
        :param board_path: path to the json file with the board.
        :return: dictionary with information about board with structure compatible with UFIV JSON file schema.
        """

        pcb_info = self.pcb.to_json() if self.pcb is not None else dict()
        if save_image_if_needed_to and self.image:
            os.makedirs(os.path.dirname(save_image_if_needed_to), exist_ok=True)
            self.image.save(save_image_if_needed_to)
            if board_path is not None:
                pcb_info["pcb_image_path"] = os.path.relpath(save_image_if_needed_to, os.path.dirname(board_path))
            else:
                pcb_info["pcb_image_path"] = save_image_if_needed_to

        data = {"elements": [element.to_json() for element in self.elements],
                "version": version}
        if pcb_info:
            data["PCB"] = pcb_info
        return data
