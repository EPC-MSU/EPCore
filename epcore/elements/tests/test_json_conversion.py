import unittest
from json import load
from os.path import dirname, join as join_path
from epcore.elements.board import Board


testfile = join_path(dirname(__file__), "testboard.json")


class JsonConversionTest(unittest.TestCase):
    def test_json_conversion(self):
        # load board
        with open(testfile, "r") as json_source:
            json_dict = load(json_source)
            board = Board.create_from_json(json_dict)
        # save to dict
        new_json_dict = board.to_json()
        self.assertTrue(new_json_dict == json_dict)
