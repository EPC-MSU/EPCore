from dataclasses import dataclass
from typing import Any, Dict, Optional, Union
from .abstract import JsonConvertible


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
