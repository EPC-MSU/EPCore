import os
import unittest
from json import load
import jsonschema
from epcore.elements.board import Board

DIR_NAME = os.path.dirname(os.path.abspath(__file__))
SCHEMA = os.path.join(os.path.dirname(os.path.dirname(DIR_NAME)), "doc", "ufiv.schema.json")
TEST_FILE = os.path.join(DIR_NAME, "testboard.json")
TEST_FILE_WITH_MULTIPLEXER_OUTPUT = os.path.join(DIR_NAME, "testboard_with_multiplexer_output.json")


class JsonConversionTest(unittest.TestCase):

    def test_json_conversion(self):
        # Load board
        with open(TEST_FILE, "r") as json_source:
            json_dict = load(json_source)
            board = Board.create_from_json(json_dict)
        # Save to dict
        new_json_dict = board.to_json()
        self.assertTrue(new_json_dict == json_dict)

    def test_json_with_multiplexer_output(self):
        """
        Test checks that from board file with multiplexer outputs will be
        created board with pins which have multiplexer outputs.
        """

        with open(SCHEMA, "r") as schema_source:
            schema = load(schema_source)
        with open(TEST_FILE_WITH_MULTIPLEXER_OUTPUT, "r") as json_source:
            json_dict = load(json_source)
            jsonschema.validate(json_dict, schema)
            board = Board.create_from_json(json_dict)
        pins_with_multiplexer_output = 0
        for element in board.elements:
            for pin in element.pins:
                if pin.multiplexer_output:
                    pins_with_multiplexer_output += 1
        self.assertTrue(pins_with_multiplexer_output == 1)

    def test_json_without_multiplexer_output(self):
        """
        Test checks that from board file with no multiplexer outputs will be
        created board with pins which have no multiplexer outputs.
        """

        with open(TEST_FILE, "r") as json_source:
            json_dict = load(json_source)
            board = Board.create_from_json(json_dict)
        pins_with_multiplexer_output = 0
        for element in board.elements:
            for pin in element.pins:
                if pin.multiplexer_output:
                    pins_with_multiplexer_output += 1
        self.assertTrue(pins_with_multiplexer_output == 0)
