"""
Operations with UFIV JSON files
UFIV - Universal file format for IV-curve measurements.
"""
import logging
from ..elements import Board

def load_board_from_ufiv(path_to_file: str) -> Board:
    # TODO Write docstring
    logging.debug("Save board to UFIV file")
    # TODO Check file existance
    # TODO Load JSON from file
    # TODO Create board
    # TODO Create readable errors if needed.
    # TODO Check image. If image is presented, do something

    return Board

def save_board_to_ufiv(path_to_file: str, board: Board):
    # TODO Write docstring
    logging.debug("Load board from UFIV file")
    # TODO Create directory if needed
    # TODO Save board to file
    # TODO Create readable errors in case of permission issues
    pass
