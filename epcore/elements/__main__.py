import logging

from .measurement import Measurement, Point, MeasurementSettings
from .pin import Pin
from .element import Element
from .board import Board

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    # Create board with elements with pins

    # Element 1
    e1 = Element(
        pins=[
            Pin(0.0, 0.0, [
                Measurement(
                    MeasurementSettings(0, 0, 0, 0),
                    ivc=[Point(0, 0), Point(1, 1)]
                ),
            ])
        ]
    )

    # Element 2
    e2 = Element(
        pins=[
            Pin(1.0, 1.0, [
                Measurement(
                    MeasurementSettings(1, 1, 1, 1),
                    ivc=[Point(6, 5), Point(4, 3)]
                ),
            ], comment="hi here")
        ]
    )

    # Board
    board = Board([e1, e2], version="1.0.0")
    print(board)

    # json conversion
    board_json = board.to_json()
    print(board_json)

    board_2 = Board.create_from_json(board_json)
    print(board)
