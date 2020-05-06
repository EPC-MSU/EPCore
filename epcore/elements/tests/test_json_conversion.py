from ..board import Board

from os.path import dirname, join as join_path

from json import load

testfile = join_path(dirname(__file__), "testboard.json")


def test_json_conversion():
    # load board
    with open(testfile, "r") as json_source:
        json_dict = load(json_source)
        board = Board.create_from_json(json_dict)

    # save to dict
    new_json_dict = board.to_json()

    assert new_json_dict == json_dict
