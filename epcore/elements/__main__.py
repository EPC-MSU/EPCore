import logging

from .measurement import Measurement
from .pin import Pin
from .element import Element
from .board import Board

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    # Create board with elements with pins
    # Element 1
    e_1 = Element([Pin([Measurement()], "E1 Pin 1"),
                   Pin([Measurement()], "E1 Pin 2"),
                   Pin([Measurement()], "E1 Pin 3")])

    # Element 2
    e_2 = Element([Pin([Measurement()], "E2 Pin 1"),
                   Pin([Measurement()], "E2 Pin 2")])

    # Board
    board = Board([e_1, e_2])

    # json conversion
    board_json = board.to_json_dict()
    print(board_json)

    board_2 = Board.create_from_json_dict(board_json)
