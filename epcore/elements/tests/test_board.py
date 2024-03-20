import json
import os
import unittest
from typing import Any, Dict
from PIL import Image, ImageOps
from epcore.elements import Board, PCBInfo


def get_data_from_json_file(json_path: str) -> Dict[str, Any]:
    """
    :param json_path: path to json file.
    :return: data from json file.
    """

    with open(json_path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_image_from_file(image_path: str) -> Image.Image:
    """
    :param image_path: path to the image file.
    :return: image.
    """

    return ImageOps.exif_transpose(Image.open(image_path))


class TestBoard(unittest.TestCase):

    dir_with_data: str = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.dir_with_data: str = os.path.join(os.path.dirname(__file__), "data_for_board_tests")

    def test_create_from_json_for_board_with_rel_path_and_image(self) -> None:
        """
        Test checks the creation of a board from a json file in which the relative path to the image is specified and
        the image is there.
        """

        json_path = os.path.join(TestBoard.dir_with_data, "board_with_rel_path_and_image", "board.json")
        json_data = get_data_from_json_file(json_path)
        board = Board.create_from_json(json_data, board_path=json_path)

        self.assertIsNotNone(board.image)
        self.assertEqual(len(board.elements), 2)
        for element, pins_number in zip(board.elements, (1, 3)):
            self.assertEqual(len(element.pins), pins_number)

        self.assertEqual(board.pcb, PCBInfo("test_board", None, None))

    def test_create_from_json_for_board_wit_rel_path_and_without_image(self) -> None:
        """
        Test checks the creation of a board from a json file in which the relative path to the image is specified and
        the image is not.
        """

        json_path = os.path.join(TestBoard.dir_with_data, "board_with_rel_path_and_without_image", "board.json")
        json_data = get_data_from_json_file(json_path)

        with self.assertRaises(FileNotFoundError):
            Board.create_from_json(json_data, board_path=json_path)

        board = Board.create_from_json(json_data, True, json_path)
        self.assertIsNone(board.image)
        self.assertEqual(len(board.elements), 2)
        for element, pins_number in zip(board.elements, (1, 3)):
            self.assertEqual(len(element.pins), pins_number)

        self.assertEqual(board.pcb, PCBInfo("test_board", None, None))

    def test_create_from_json_for_board_without_rel_path_and_image(self) -> None:
        """
        Test checks the creation of a board from a json file in which the relative path to the image is not specified,
        but the image is there.
        """

        json_path = os.path.join(TestBoard.dir_with_data, "board_without_rel_path_and_image", "board.json")
        json_data = get_data_from_json_file(json_path)
        board = Board.create_from_json(json_data)

        self.assertIsNone(board.image)
        self.assertEqual(len(board.elements), 2)
        for element, pins_number in zip(board.elements, (1, 3)):
            self.assertEqual(len(element.pins), pins_number)

        self.assertEqual(board.pcb, PCBInfo(None, None, None))

    def test_to_json_with_image(self) -> None:
        """
        Test checks the conversion of the board into json data. The board has an image.
        """

        image = get_image_from_file(os.path.join(TestBoard.dir_with_data, "test_image.png"))
        image_path = os.path.join(TestBoard.dir_with_data, "test_1", "test_2", "image_name.png")
        board_path = os.path.join(TestBoard.dir_with_data, "test_1", "board.json")

        board = Board(elements=[], image=image, pcb=PCBInfo("test_board", 23.0, "comment"))
        json_data = board.to_json(save_image_if_needed_to=image_path, board_path=board_path)
        self.assertEqual(json_data, {"PCB": {"pcb_name": "test_board",
                                             "image_resolution_ppcm": 23.0,
                                             "comment": "comment",
                                             "pcb_image_path": os.path.join("test_2", "image_name.png")},
                                     "elements": [],
                                     "version": "1.1.2"})
        self.assertTrue(os.path.isdir(os.path.dirname(image_path)))
        self.assertTrue(os.path.isfile(image_path))

        json_data = board.to_json()
        self.assertEqual(json_data, {"PCB": {"pcb_name": "test_board",
                                             "image_resolution_ppcm": 23.0,
                                             "comment": "comment"},
                                     "elements": [],
                                     "version": "1.1.2"})

    def test_to_json_without_image(self) -> None:
        """
        Test checks the conversion of the board into json data. The board has no image.
        """

        board = Board(elements=[], image=None, pcb=PCBInfo("test_board", 23.0, "comment"))
        json_data = board.to_json()
        self.assertEqual(json_data, {"PCB": {"pcb_name": "test_board",
                                             "image_resolution_ppcm": 23.0,
                                             "comment": "comment"},
                                     "elements": [],
                                     "version": "1.1.2"})

        json_data = board.to_json(save_image_if_needed_to="some_path", board_path="other_path")
        self.assertEqual(json_data, {"PCB": {"pcb_name": "test_board",
                                             "image_resolution_ppcm": 23.0,
                                             "comment": "comment"},
                                     "elements": [],
                                     "version": "1.1.2"})
