"""
Operations with UFIV JSON files
UFIV - Universal file format for IV-curve measurements.
"""
from ..elements import Board, version
from ..utils import convert_p10, convert_p10_2
from ..doc import path_to_ufiv_schema, path_to_p10_elements_schema, path_to_p10_elements_2_schema
from os.path import isfile
import os
from json import load, dump
import logging
from typing import Dict
from PIL import Image
from jsonschema import validate, ValidationError
import enum
from os.path import basename
import zipfile
from tempfile import TemporaryDirectory

MAX_ERR_MSG_LEN = 256


class FileUFIVFormat:
    json_pth = ""
    img_pth = ""

    def __init__(self, json_pth=None):
        self.json_pth = json_pth
        if json_pth is None:
            return

        self.find_img()

    def add_img_pth(self, img_pth):
        self.img_pth = img_pth

    def find_img(self):
        dir = os.path.dirname(self.json_pth)
        for f in os.listdir(dir):
            if ".png" in f or ".jpg" in f or ".bmp" in f:
                if f[:-4] == basename(self.json_pth)[:-5]:
                    self.add_img_pth(os.path.join(dir, f))

    def get_json_and_image(self):
        with open(self.json_pth, "r") as file:
            input_json = load(file)
        if self.img_pth is not None:
            image = Image.open(self.img_pth) if isfile(self.img_pth) else None
        return input_json, image


class FileP10NormalFormat(FileUFIVFormat):

    def __init__(self, path):
        super().__init__(json_pth=path)
        _dir = os.path.dirname(self.json_pth)
        if not isfile(self.img_pth):
            self.add_img_pth(os.path.join(_dir, "image.png"))

    def get_json_and_image(self, p10_convert_flag):
        input_json, image = super().get_json_and_image()
        if p10_convert_flag:
            input_json = convert_p10(input_json, version=version, force_reference=True)
        return input_json, image


class FileP10NewFormat(FileUFIVFormat):

    def __init__(self, path):
        super().__init__(json_pth=path)
        _dir = os.path.dirname(self.json_pth)
        if not isfile(self.img_pth):
            self.add_img_pth(os.path.join(_dir, "image.png"))

    def get_json_and_image(self, p10_convert_flag):
        input_json, image = super().get_json_and_image()
        if p10_convert_flag:
            input_json = convert_p10_2(input_json, version=version, force_reference=True)
        return input_json, image


class FileArchivedUFIVFormat(FileUFIVFormat):

    def __init__(self, path):
        json_pth = self.convert_to_ufiv(path)
        super().__init__(json_pth=json_pth)

    def convert_to_ufiv(self, path):
        """
        Function convert UFIV_archived format to UFIV
        :param path:
        :return:
        """
        archive = zipfile.ZipFile(path, "r")
        tempdir = TemporaryDirectory().name
        archive.extractall(path=tempdir)
        archive.close()
        return os.path.join(tempdir, basename(path).replace(".uzf", ".json"))


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
    """
    try:
        validate(input_json, validation_schema)
    except ValidationError as err:
        err.message = "The input file has invalid format: " + err.message[:MAX_ERR_MSG_LEN]
        raise


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

        validation_error = None
        json_format = Formats.Normal_P10
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
                    json_format = Formats.New_P10
                    validation_error = None
                except ValidationError as e:
                    validation_error = e

            # We did not found correct format
            if validation_error is not None:
                raise validation_error
    else:
        json_format = Formats.UFIV
    return json_format


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

        _validate_json_with_schema(input_json, ufiv_schema_json)  # check input_json has ufiv format
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
            archive.write(source_file.img_pth, arcname=basename(source_file.img_pth).replace(basename(source_file.img_pth)[:-4], basename(source_file.json_pth)[:-5]))
        else:
            archive.write(source_file.img_pth, arcname=basename(source_file.img_pth).replace(basename(source_file.img_pth)[:-4], basename(source_file.json_pth)[:-5]))
    archive.close()
