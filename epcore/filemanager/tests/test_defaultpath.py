import unittest
from epcore.filemanager import DefaultPathManager, DefaultPathError
import tempfile
from os.path import join, isdir
from os import makedirs


class DefaultPathTest(unittest.TestCase):
    def test_nonexistent_path(self):
        manager = DefaultPathManager("/DUMMY_PATH_NOT_EXISTS")
        with self.assertRaises(DefaultPathError):
            manager.save_file_path()
        with self.assertRaises(DefaultPathError):
            manager.open_file_path()

    def test_normal_path(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = DefaultPathManager(directory)
            manager.save_file_path()
            manager.open_file_path()

    def test_create_subdirs(self):
        with tempfile.TemporaryDirectory() as directory:
            subdirs = join("foo", "bar", "spam")
            manager = DefaultPathManager(directory, subdirs)
            s_path = manager.save_file_path()
            self.assertTrue(isdir(join(directory, subdirs)))
            self.assertTrue(subdirs in s_path)

    def _write_dummy_file(self, path: str):
        with open(path, "w") as file:
            file.write("test")

    def test_save_names(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = DefaultPathManager(directory)
            file1 = manager.save_file_path()
            self._write_dummy_file(file1)
            file2 = manager.save_file_path()
            self._write_dummy_file(file2)
            file3 = manager.save_file_path()
            self._write_dummy_file(file3)

            self.assertTrue(file1 != file2 and file2 != file3 and file3 != file1)

    def test_open_name_no_files(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = DefaultPathManager(directory, "foo")
            self.assertTrue(manager.open_file_path() is None)

    def test_open_name(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = DefaultPathManager(directory, "bar")
            file1 = manager.save_file_path()
            self._write_dummy_file(file1)
            self.assertTrue(manager.open_file_path())

    def test_random_files(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = DefaultPathManager(directory)
            self._write_dummy_file(join(directory, "random_file_1"))
            self._write_dummy_file(join(directory, "file_2.json"))
            makedirs(join(directory, "rand_dir"))

            self.assertTrue(manager.open_file_path() is None)

    def test_default_available(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = DefaultPathManager(directory)
            self.assertTrue(manager.is_default_path_available())

        manager = DefaultPathManager("/DUMMY_PATH_NOT_EXISTS")
        self.assertTrue(not manager.is_default_path_available())
