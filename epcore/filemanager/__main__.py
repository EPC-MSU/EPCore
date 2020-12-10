from ..elements import Board, Element
from .ufiv import load_board_from_ufiv, save_board_to_ufiv
from .defaultpath import DefaultPathManager
from pathlib import Path


if __name__ == "__main__":

    # Create ur own board here
    board = Board([Element([])])

    # Save board to file
    save_board_to_ufiv("test.json", board)

    # Read board from file
    # If "test.png" is next to "test.json" board image will be loaded
    board_2 = load_board_from_ufiv("test.json")

    # Get default path for new board
    manager = DefaultPathManager(str(Path.home()), "my_boards")
    save_board_to_ufiv(manager.save_file_path(), board)
    save_board_to_ufiv(manager.save_file_path(), board)  # will assign a number, will not replace the previous file
