from ..measurement import Measurement, Point, MeasurementSettings
from ..pin import Pin
from ..element import Element
from ..board import Board


def test_json_conversion():
    # Create some elements
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
    board1 = Board([e1, e2])

    # convert board to json
    output_json_1 = board1.to_json()

    # create board from json!
    board2 = Board.create_from_json(output_json_1)

    # ... and another one!
    output_json_2 = board2.to_json()

    assert (output_json_1 == output_json_2)
