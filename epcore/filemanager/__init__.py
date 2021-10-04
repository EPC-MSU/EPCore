"""
EyePoint module for file IO operations.

To run example:
python -m epcore.filemanager

To build documentaion:
pydoc -w epcore.filemanager

To run tests:
python -m unittest discover epcore/filemanager
"""

from .defaultpath import DefaultPathError, DefaultPathManager
from .ufiv import add_image_to_ufiv, load_board_from_ufiv, save_board_to_ufiv

__all__ = ["add_image_to_ufiv",
           "DefaultPathError",
           "DefaultPathManager",
           "load_board_from_ufiv",
           "save_board_to_ufiv"]

__author__ = "mihalin"
__email__ = "mihalin@physlab.ru"
