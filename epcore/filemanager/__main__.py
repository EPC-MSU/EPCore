from ..elements import Board
from .ufiv import load_board_from_ufiv, save_board_to_ufiv

if __name__ == "__main__":

    # Create ur own board here
    board = Board([])

    # Save board to file
    save_board_to_ufiv("test.json", board)

    # Read board from file
    # If "test.png" is next to "test.json" board image will be loaded
    board_2 = load_board_from_ufiv("test.json")
