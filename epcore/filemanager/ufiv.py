"""
Operations with UFIV JSON files
UFIV - Universal file format for IV-curve measurements.
"""
from ..elements import Board
from .file_formats import FileUFIVFormat, FileP10NormalFormat, FileP10NewFormat, FileArchivedUFIVFormat
from ..doc import path_to_ufiv_schema, path_to_p10_elements_schema, path_to_p10_elements_2_schema
from os.path import isfile, basename
import os
from json import load, dump
import logging
from typing import Dict
from PIL import Image
from jsonschema import validate, ValidationError
import enum
import zipfile
from tempfile import TemporaryDirectory

MAX_ERR_MSG_LEN = 256


class Formats(enum.Enum):
    Normal_P10 = 0
    New_P10 = 1
    UFIV = 2
    UFIV_archived = 3


formats_to_file = {
    Formats.UFIV: FileUFIVFormat,
    Formats.Normal_P10: FileP10NormalFormat,
    Formats.New_P10: FileP10NewFormat,
    Formats.UFIV_archived: FileArchivedUFIVFormat
}

source_file = FileUFIVFormat()


def _validate_json_with_schema(input_json: Dict, validation_schema: Dict):
    """
    Validate json. Raise Validation Error in case of invalid json.
    :param input_json: json to be validated
    :param json: json schema for validation
    :return: is_valid, error
    """
    try:
        validate(input_json, validation_schema)
        return True, None
    except ValidationError as err:
        err.message = "The input file has invalid format: " + err.message[:MAX_ERR_MSG_LEN]
        return False, err


def detect_format(path: str, validate_input: bool = True):
    """
    Returned format of board file
    :param path:
    :param validate_input:
    :return:
    """
    if ".uzf" in path:
        return Formats.UFIV_archived

    with open(path, "r") as file:
        input_json = load(file)

    # Convert from old format if needed
    if "version" not in input_json:
        # Old format. Should be converted first.
        logging.info("No 'version' key found, try to convert board from P10 format...")

        if validate_input:

            logging.info("Check normal P10 format.")
            with open(path_to_p10_elements_schema(), "r") as schema_file:
                p10_elements_schema_json = load(schema_file)
            is_valid, err = _validate_json_with_schema(input_json, p10_elements_schema_json)
            if is_valid:
                return Formats.Normal_P10

            logging.info("Check alternative P10 format.")
            with open(path_to_p10_elements_2_schema(), "r") as schema_2_file:
                p10_elements_schema_2_json = load(schema_2_file)
            is_valid, err = _validate_json_with_schema(input_json, p10_elements_schema_2_json)
            if is_valid:
                return Formats.New_P10
            else:
                raise err
    else:
        return Formats.UFIV


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
    global source_file
    _format = detect_format(path, validate_input)
    source_file = formats_to_file[_format](path)
    if _format is Formats.Normal_P10 or _format is Formats.New_P10:
        input_json, image = source_file.get_json_and_image(auto_convert_p10)
    else:
        input_json, image = source_file.get_json_and_image()
    if validate_input:
        with open(path_to_ufiv_schema(), "r") as schema_file:
            ufiv_schema_json = load(schema_file)

    is_valid, err = _validate_json_with_schema(input_json, ufiv_schema_json)  # check input_json has ufiv format
    if not is_valid:
        raise err
    board = Board.create_from_json(input_json)
    board.image = image

    return board


def add_image_to_ufiv(path: str, board: Board) -> Board:
    """
    Add board image to existing board
    :param path:
    :param board:
    :return:
    """
    global source_file
    board.image = Image.open(path)
    source_file.add_img_pth(path)
    return board


def save_board_to_ufiv(path_to_file: str, board: Board):
    """
    Save board(png, json) files
    :param path_to_file:
    :param board:
    :return:
    """
    global source_file
    if ".json" in path_to_file:
        path_to_file = path_to_file.replace(".json", ".uzf")
    t = TemporaryDirectory()
    source_file.json_pth = os.path.join(t.name, basename(path_to_file.replace(".uzf", ".json")))
    json = board.to_json()
    archive = zipfile.ZipFile(path_to_file, "w")
    with open(source_file.json_pth, "w") as file:
        dump(json, file, indent=1)
    archive.write(source_file.json_pth, arcname=basename(source_file.json_pth))
    if board.image is not None:
        if not isfile(source_file.img_pth):
            board.image.save(source_file.img_pth)
            archive.write(source_file.img_pth,
                          arcname=basename(source_file.img_pth).replace(basename(source_file.img_pth)[:-4],
                          basename(source_file.json_pth)[:-5]))
        else:
            archive.write(source_file.img_pth,
                          arcname=basename(source_file.img_pth).replace(basename(source_file.img_pth)[:-4],
                          basename(source_file.json_pth)[:-5]))
    archive.close()
