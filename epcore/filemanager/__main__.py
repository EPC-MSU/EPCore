import logging
from ..elements import Board
from .ufiv import load_board_from_ufiv, save_board_to_ufiv

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    board = Board()
    save_board_to_ufiv("test.json", board)
    board_2 = load_board_from_ufiv("test.json")

