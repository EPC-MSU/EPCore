"""
Operations with UFIV JSON files
UFIV - Universal file format for IV-curve measurements.
"""
from ..elements import Board
from os.path import isfile
from json import load, dump
from PyQt5.QtGui import QImage


def load_board_from_ufiv(path: str) -> Board:
    """
    Load board (json, png) from directory
    :param path: path to directory with board
    :return:
    """

    with open(path, "r") as file:
        board = Board.create_from_json(load(file))

    image_path = path.replace(".json", ".png")
    if isfile(image_path):
        board.image = QImage(image_path)

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