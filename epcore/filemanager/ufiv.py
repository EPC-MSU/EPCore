"""
Operations with UFIV JSON files
UFIV - Universal file format for IV-curve measurements.
"""
from ..elements import Board, version
from ..utils import convert_p10, convert_p10_2
from ..doc import path_to_ufiv_schema, path_to_p10_elements_schema, path_to_p10_elements_2_schema
from os.path import isfile
from json import load, dump
import logging
from typing import Dict
from PIL import Image
from jsonschema import validate, ValidationError
from os.path import basename

MAX_ERR_MSG_LEN = 256


def _validate_json_with_schema(input_json: Dict, validation_schema: Dict):
    """
    Validate json. Raise Validation Error in case of invalid json.
    :param input_json: json to be validated
    :param json: json schema for validation
    """
    try:
        validate(input_json, validation_schema)
    except ValidationError as err:
        err.message = "The input file has invalid format: " + err.message[:MAX_ERR_MSG_LEN]
        raise


def load_board_from_ufiv(path: str,
                         validate_input: bool = True,
                         auto_convert_p10: bool = True) -> Board:
    """
    Load board (json and png) from directory
    :param path: path to JSON file
    :param validate_input: validate JSON before load
    :param auto_convert_p10: enable auto conversion p10->ufiv
    :return:
    """
    with open(path, "r") as file:
        input_json = load(file)

    # Convert from old format if needed
    if "version" not in input_json and auto_convert_p10:
        # Old format. Should be converted first.
        logging.info("No 'version' key found, try to convert board from P10 format...")

        validation_error = None
        p10_fomat = "Normal_Schema"
        if validate_input:
            logging.info("Check normal P10 format.")
            try:
                with open(path_to_p10_elements_schema(), "r") as schema_file:
                    p10_elements_schema_json = load(schema_file)

                _validate_json_with_schema(input_json, p10_elements_schema_json)
            except ValidationError as e:
                validation_error = e

            # If failed check an other format
            logging.info("Check alternative P10 format.")
            if validation_error is not None:
                try:
                    with open(path_to_p10_elements_2_schema(), "r") as schema_2_file:
                        p10_elements_schema_2_json = load(schema_2_file)

                    _validate_json_with_schema(input_json, p10_elements_schema_2_json)
                    p10_fomat = "Schema_2"
                    validation_error = None
                except ValidationError as e:
                    validation_error = e

            # We did not found correct format
            if validation_error is not None:
                raise validation_error

        if p10_fomat == "Normal_Schema":
            input_json = convert_p10(input_json, version=version, force_reference=True)

        if p10_fomat == "Schema_2":
            input_json = convert_p10_2(input_json, version=version, force_reference=True)

    if validate_input:
        with open(path_to_ufiv_schema(), "r") as schema_file:
            ufiv_schema_json = load(schema_file)

        _validate_json_with_schema(input_json, ufiv_schema_json)

    board = Board.create_from_json(input_json)

    image_path = path.replace(".json", ".png")
    # Old-style format used 'image.png' files near elements.json file
    p10_image_path = path.replace(basename(path), "image.png")
    if isfile(image_path):
        board.image = Image.open(image_path)
    elif auto_convert_p10:
        if isfile(p10_image_path):
            board.image = Image.open(p10_image_path)

    return board


def add_image_to_ufiv(path: str, board: Board) -> Board:
    """
    Add board image to existing board
    :param path:
    :param board:
    :return:
    """
    board.image = Image.open(path)
    return board


def save_board_to_ufiv(path_to_file: str, board: Board):
    """
    Save board(png, json) files
    :param path_to_file:
    :param board:
    :return:
    """

    json = board.to_json()

    with open(path_to_file, "w") as file:
        dump(json, file)

    image_path = path_to_file.replace(".json", ".png")

    if board.image is not None:
        board.image.save(image_path)
