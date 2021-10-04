from .board import Board
from .element import Element
from .measurement import IVCurve, Measurement, MeasurementSettings
from .pin import Pin


if __name__ == "__main__":
    # Create board with elements with pins

    # Element 1
    e1 = Element(
        pins=[Pin(0.0, 0.0, [Measurement(MeasurementSettings(0, 0, 0, 0),
                                         ivc=IVCurve(currents=[1, 2, 3], voltages=[4, 5, 6]))])])

    # Element 2
    e2 = Element(
        pins=[Pin(1.0, 1.0, [Measurement(MeasurementSettings(1, 1, 1, 1),
                                         ivc=IVCurve(currents=[1, 2, 3], voltages=[6, 4, 2]))],
                  comment="Some comment for pin")])

    # Board
    board = Board([e1, e2])
    print(board)

    # Json conversion
    board_json = board.to_json()
    print(board_json)

    board_2 = Board.create_from_json(board_json)
    print(board)
