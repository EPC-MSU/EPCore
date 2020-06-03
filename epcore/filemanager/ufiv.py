"""
Operations with UFIV JSON files
UFIV - Universal file format for IV-curve measurements.
"""
from ..elements import Board, version
from ..utils import convert_p10
from os.path import isfile
from json import load, dump
from logging import warning
from PIL import Image
from jsonschema import validate, ValidationError
from os.path import basename
from ..doc import path_to_ufiv_schema


def load_board_from_ufiv(path: str,
                         validate_input: bool = True, 
                         auto_convert_p10: bool = True) -> Board:
    """
    Load board (json and png) from directory
    :param path: path to JSON file
    :validate_input: validate JSON before load
    :param auto_convert_p10: enable auto conversion p10->ufiv
    :return:
    """
    with open(path, "r") as file:
        input_json = load(file)

    if "version" not in input_json and auto_convert_p10:
        warning("No 'version' key found, try to convert board from P10 format...")
        input_json = convert_p10(input_json, version=version, force_reference=True)

    if validate_input:
        with open(path_to_ufiv_schema(), "r") as schema_file:
           ufiv_schema_json = load(schema_file)
        
        try:
            validate(input_json, ufiv_schema_json)
        except ValidationError as err:
            err.message = "The input file has invalid format: " + err.message
            raise

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
