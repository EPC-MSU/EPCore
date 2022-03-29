"""
Operations with UFIV JSON files.
UFIV - Universal file format for IV-curve measurements.
"""

import enum
import logging
import os
import re
import zipfile
from json import load, dump
from tempfile import TemporaryDirectory
from typing import Dict, Optional, Tuple
from jsonschema import validate, ValidationError
from PIL import Image
from ..doc import path_to_ufiv_schema, path_to_p10_elements_schema, path_to_p10_elements_2_schema
from ..elements import Board
from .file_formats import (FileArchivedUFIVFormat, FileP10NewFormat, FileP10NormalFormat,
                           FileUFIVFormat)


MAX_ERR_MSG_LEN = 256
# Path to the last image of board
_image_path: str = None


class Formats(enum.Enum):
    NORMAL_P10 = 0
    NEW_P10 = 1
    UFIV = 2
    UFIV_ARCHIVED = 3


formats_to_file = {
    Formats.UFIV: FileUFIVFormat,
    Formats.NORMAL_P10: FileP10NormalFormat,
    Formats.NEW_P10: FileP10NewFormat,
    Formats.UFIV_ARCHIVED: FileArchivedUFIVFormat
}


def _check_json_data_for_ufiv_format(json_data: Dict) -> Dict:
    """
    Function checks json data to be saved in ufiv format file. If data
    does not match ufiv format, function will fit the data to format.
    :param json_data: data.
    :return: modified data.
    """

    elements = json_data.get("elements", [])
    for element in elements:
        bounding_zone = element.get("bounding_zone")
        if not bounding_zone and "bounding_zone" in element:
            element.pop("bounding_zone")
    return json_data


def _validate_json_with_schema(input_json: Dict, schema: Dict) -> Tuple[bool, Optional[Exception]]:
    """
    Function validates json. Raise ValidationError in case of invalid json.
    :param input_json: json to be validated;
    :param schema: json schema for validation.
    :return: is_valid, error.
    """

    try:
        validate(input_json, schema)
        return True, None
    except ValidationError as err:
        err.message = ("The input file has invalid format: " + err.message[:MAX_ERR_MSG_LEN])
        return False, err


def add_image_to_ufiv(path: str, board: Board) -> Board:
    """
    Function adds board image to existing board.
    :param path: path to image;
    :param board: board to which the image should be added.
    :return: board.
    """

    global _image_path
    _image_path = path
    board.image = Image.open(path)
    return board


def detect_format(path: str) -> Formats:
    """
    Function returns format of board file.
    :param path: path to board file.
    :return: format of board file.
    """

    if ".uzf" in path:
        return Formats.UFIV_ARCHIVED
    with open(path, "r") as file:
        input_json = load(file)
    if "version" not in input_json:
        # Old format. Should be converted first
        logging.info("Key 'version' not found, try to convert board from P10 format...")
        logging.info("Check normal P10 format.")
        with open(path_to_p10_elements_schema(), "r") as schema_file:
            p10_schema = load(schema_file)
        is_valid, err = _validate_json_with_schema(input_json, p10_schema)
        if is_valid:
            return Formats.NORMAL_P10
        logging.info("Check alternative P10 format.")
        with open(path_to_p10_elements_2_schema(), "r") as schema_file:
            p10_new_schema = load(schema_file)
        is_valid, err = _validate_json_with_schema(input_json, p10_new_schema)
        if is_valid:
            return Formats.NEW_P10
        raise err
    return Formats.UFIV


def load_board_from_ufiv(path: str, validate_input: bool = True,
                         auto_convert_p10: bool = True) -> Board:
    """
    Function loads board (json and png) from directory.
    :param path: path to json file;
    :param validate_input: if True function validates json content to schema
    before load;
    :param auto_convert_p10: enable auto conversion p10->ufiv.
    :return: board.
    """

    global _image_path
    _format = detect_format(path)
    source_file = formats_to_file[_format](path)
    _image_path = source_file.img_pth
    if _format is Formats.NORMAL_P10 or _format is Formats.NEW_P10:
        input_json, image = source_file.get_json_and_image(auto_convert_p10)
    else:
        input_json, image = source_file.get_json_and_image()
    if validate_input:
        with open(path_to_ufiv_schema(), "r") as schema_file:
            ufiv_schema = load(schema_file)
            is_valid, err = _validate_json_with_schema(input_json, ufiv_schema)
            if not is_valid:
                raise err
    board = Board.create_from_json(input_json)
    board.image = image
    return board


def save_board_to_ufiv(path: str, board: Board) -> str:
    """
    Function saves board (png, json) files.
    :param path: path to saved file;
    :param board: board that should be saved.
    :return: path to saved file.
    """

    if not re.match(r"^.*\.uzf$", path):
        path += ".uzf"
    temp_dir = TemporaryDirectory()
    archive = zipfile.ZipFile(path, "w")
    # Save json file in archive
    json_name = os.path.basename(path.replace(".uzf", ".json"))
    json_path = os.path.join(temp_dir.name, json_name)
    json_file = _check_json_data_for_ufiv_format(board.to_json())
    with open(json_path, "w") as file:
        dump(json_file, file, indent=1)
    archive.write(json_path, arcname=json_name)
    # Save image in archive
    img_name = os.path.basename(path.replace(".uzf", ".png"))
    if board.image:
        if not _image_path:
            img_path = os.path.join(temp_dir.name, img_name)
            board.image.save(img_path)
        else:
            img_path = _image_path
        archive.write(img_path, arcname=img_name)
    archive.close()
    return path
