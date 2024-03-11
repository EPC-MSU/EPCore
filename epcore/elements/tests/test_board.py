import unittest
from epcore.elements import Board


class TestBoard(unittest.TestCase):

    def test_create_from_json(self) -> None:
        json_data = {"version": "1.1.2",
                     "elements": []}
        board = Board.create_from_json(json_data)
        self.assertIsNone(board.pcb.comment)
        self.assertIsNone(board.pcb.image_resolution_ppcm)
        self.assertIsNone(board.pcb.pcb_name)
        self.assertEqual(len(board.elements), 0)
