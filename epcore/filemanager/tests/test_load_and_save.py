import os
import unittest
import zipfile
from tempfile import TemporaryDirectory
from jsonschema import ValidationError
from PIL import Image
from epcore.elements import Board
from epcore.filemanager import load_board_from_ufiv, save_board_to_ufiv


class LoadSaveTests(unittest.TestCase):

    dir_path: str = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.dir_path: str = os.path.join(os.path.dirname(__file__), "data")

    def test_load_board_from_ufiv_format_ufiv(self) -> None:
        board_path = os.path.join(LoadSaveTests.dir_path, "ufiv_format", "testboard.json")
        board = load_board_from_ufiv(board_path)
        self.assertIsNotNone(board.image)
        self.assertEqual(board.image.width, 100)
        self.assertEqual(board.image.height, 100)

    def test_load_board_from_ufiv_old_style_format(self) -> None:
        old_style_board_path = os.path.join(LoadSaveTests.dir_path, "old_style_board.json")
        board = load_board_from_ufiv(old_style_board_path, auto_convert_p10=True)
        self.assertTrue(bool(board))

    def test_load_board_from_ufiv_old_style_format_validation(self):
        invalid_old_style_board_path = os.path.join(LoadSaveTests.dir_path, "old_style_board_invalid.json")
        with self.assertRaises(ValidationError):
            load_board_from_ufiv(invalid_old_style_board_path, auto_convert_p10=True, validate_input=True)

    def test_load_board_from_ufiv_old_style_board_with_image(self) -> None:
        old_style_board_with_img_path = os.path.join(LoadSaveTests.dir_path, "testboard_with_img", "board.json")
        board = load_board_from_ufiv(old_style_board_with_img_path)
        self.assertTrue(bool(board.image))

    def test_load_board_from_ufov_old_style_board_without_image(self) -> None:
        old_style_board_without_img_path = os.path.join(LoadSaveTests.dir_path, "testboard_without_img", "board.json")
        board = load_board_from_ufiv(old_style_board_without_img_path)
        self.assertFalse(bool(board.image))

    def test_load_board_from_ufiv_path_not_exists(self) -> None:
        dummy_path = os.path.join(LoadSaveTests.dir_path, "no_such_file.json")
        with self.assertRaises(FileNotFoundError):
            load_board_from_ufiv(dummy_path)

    def test_load_board_from_ufiv_with_rel_path_and_image(self) -> None:
        board_path = os.path.join(LoadSaveTests.dir_path, "board_with_rel_path_and_image", "board.json")
        board = load_board_from_ufiv(board_path)
        self.assertIsNotNone(board)

    def test_load_board_from_ufiv_with_rel_path_and_without_image(self) -> None:
        board_path = os.path.join(LoadSaveTests.dir_path, "board_with_rel_path_and_without_image", "board.json")
        with self.assertRaises(FileNotFoundError):
            load_board_from_ufiv(board_path)

    def test_load_board_from_ufiv_validation(self) -> None:
        invalid_board_path = os.path.join(LoadSaveTests.dir_path, "test_board_invalid.json")
        with self.assertRaises(ValidationError):
            load_board_from_ufiv(invalid_board_path, validate_input=True)

    def test_save_board_to_ufiv(self) -> None:
        image_path = os.path.join(LoadSaveTests.dir_path, "ufiv_format", "testboard.png")
        image = Image.open(image_path)
        board = Board(elements=[], image=image)

        with TemporaryDirectory() as tempdir:
            save_board_to_ufiv(os.path.join(tempdir, "foo.uzf"), board)
            self.assertTrue(os.path.isfile(os.path.join(tempdir, "foo.uzf")))
            archive = zipfile.ZipFile(os.path.join(tempdir, "foo.uzf"))
            archive.close()
            files = archive.namelist()
            self.assertTrue("foo.json" in files)
            self.assertTrue("foo.png" in files)
