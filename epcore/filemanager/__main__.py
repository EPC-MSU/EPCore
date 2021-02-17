from ..elements import Board, Element
from .ufiv import load_board_from_ufiv, save_board_to_ufiv
from .defaultpath import DefaultPathManager
from pathlib import Path
import os
import logging


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)-8s %(message)s")

    # Create our own board here
    board = Board([Element([])])

    # Save board to 'test.uzf' file
    logging.info("Save board to 'test.uzf' file")
    save_board_to_ufiv("test.uzf", board)

    # Read board from file
    # If "test.png" is next to "test.json" in "test.uzf" archiveboard image will be loaded
    logging.info("Load board from 'test.uzf' file")
    board_2 = load_board_from_ufiv("test.uzf")

    # Get default path for new board
    logging.info("Test default path and auto name generation for files")
    manager = DefaultPathManager(str(Path.home()), "my_boards")
    save_board_to_ufiv(manager.save_file_path(), board)
    save_board_to_ufiv(manager.save_file_path(), board)  # will assign a number, will not replace the previous file
    logging.info("Two boards saved to " + str(os.path.join(Path.home(), "my_boards")))
