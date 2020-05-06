import unittest
from os.path import join as join_path, dirname
from PyQt5.QtGui import QImage
from tempfile import TemporaryDirectory
from os.path import isfile
from epcore.filemanager import load_board_from_ufiv, save_board_to_ufiv
from epcore.elements import Board


board_path = join_path(dirname(__file__), "testboard.json")
dummy_path = join_path(dirname(__file__), "no_such_file.json")
image_path = join_path(dirname(__file__), "testboard.png")


class LoadSaveTests(unittest.TestCase):
    def test_path_not_exists(self):
        with self.assertRaises(FileNotFoundError):
            load_board_from_ufiv(dummy_path)

    def test_normal_board(self):
        board = load_board_from_ufiv(board_path)
        self.assertTrue(board.image is not None)
        self.assertTrue(board.image.width() == 100)
        self.assertTrue(board.image.height() == 100)

    def test_save_board(self):
        board = Board([])
        board.image = QImage(image_path)

        with TemporaryDirectory() as tempdir:
            save_board_to_ufiv(join_path(tempdir, "foo.json"), board)
            self.assertTrue(isfile(join_path(tempdir, "foo.json")))
            self.assertTrue(isfile(join_path(tempdir, "foo.png")))
