import pytest
from os.path import join as join_path, dirname
from PyQt5.QtGui import QPixmap
from tempfile import TemporaryDirectory
from os.path import isfile
from epcore.filemanager import load_board_from_ufiv, save_board_to_ufiv
from epcore.elements import Board


board_path = join_path(dirname(__file__), "testboard.json")
dummy_path = join_path(dirname(__file__), "no_such_file.json")
image_path = join_path(dirname(__file__), "testboard.png")


def test_path_not_exists():
    with pytest.raises(FileNotFoundError):
        load_board_from_ufiv(dummy_path)


def test_normal_board():
    board = load_board_from_ufiv(board_path)
    assert board.image is not None
    assert board.image.width() == 100
    assert board.image.height() == 100


def test_save_board():
    board = Board([])
    board.image = QPixmap(image_path)

    with TemporaryDirectory() as tempdir:
        save_board_to_ufiv(join_path(tempdir, "foo.json"), board)
        assert isfile(join_path(tempdir, "foo.json"))
        assert isfile(join_path(tempdir, "foo.png"))
