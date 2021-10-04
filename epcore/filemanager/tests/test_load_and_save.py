import os
import unittest
import zipfile
from tempfile import TemporaryDirectory
from jsonschema import ValidationError
from PIL import Image
from epcore.elements import Board
from epcore.filemanager import load_board_from_ufiv, save_board_to_ufiv


board_path = os.path.join(os.path.dirname(__file__), "testboard.json")
invalid_board_path = os.path.join(os.path.dirname(__file__), "testboard_invalid.json")
oldstyle_board_path = os.path.join(os.path.dirname(__file__), "oldstyleboard.json")
invalid_oldstyle_board_path = os.path.join(os.path.dirname(__file__), "oldstyleboard_invalid.json")
dummy_path = os.path.join(os.path.dirname(__file__), "no_such_file.json")
image_path = os.path.join(os.path.dirname(__file__), "testboard.png")
oldstyle_board_with_img_path = os.path.join(os.path.dirname(__file__), "testboard_with_img",
                                            "board.json")
oldstyle_board_without_img_path = os.path.join(os.path.dirname(__file__), "testboard_without_img",
                                               "board.json")


class LoadSaveTests(unittest.TestCase):
    def test_path_not_exists(self):
        with self.assertRaises(FileNotFoundError):
            load_board_from_ufiv(dummy_path)

    def test_load_board(self):
        board = load_board_from_ufiv(board_path)
        self.assertTrue(board.image is not None)
        self.assertTrue(board.image.width == 100)
        self.assertTrue(board.image.height == 100)

    def test_oldstyle_load(self):
        board = load_board_from_ufiv(oldstyle_board_path, auto_convert_p10=True)
        self.assertTrue(bool(board))

    def test_load_validation(self):
        # Bad board should cause an exception
        with self.assertRaises(ValidationError):
            load_board_from_ufiv(invalid_board_path, validate_input=True)

    def test_oldstyle_load_validation(self):
        # Bad board should cause an exception
        with self.assertRaises(ValidationError):
            load_board_from_ufiv(invalid_oldstyle_board_path, auto_convert_p10=True,
                                 validate_input=True)

    def test_save_board(self):
        board = Board([])
        board.image = Image.open(image_path)

        with TemporaryDirectory() as tempdir:
            save_board_to_ufiv(os.path.join(tempdir, "foo.uzf"), board)
            self.assertTrue(os.path.isfile(os.path.join(tempdir, "foo.uzf")))
            archive = zipfile.ZipFile(os.path.join(tempdir, "foo.uzf"))
            archive.close()
            files = archive.namelist()
            self.assertTrue("foo.json" in files)
            self.assertTrue("foo.png" in files)

    def test_load_old_style_board_with_image(self):
        board = load_board_from_ufiv(oldstyle_board_with_img_path)
        self.assertTrue(bool(board.image))

    def test_load_old_style_board_without_image(self):
        board = load_board_from_ufiv(oldstyle_board_without_img_path)
        self.assertFalse(bool(board.image))
