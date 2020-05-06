"""
EyePoint module for file IO operations.

To run example:
python -m epcore.filemanager

To build documentaion:
pydoc -w epcore.filemanager

To run tests:
python -m unittest discover epcore/filemanager
"""

from .ufiv import load_board_from_ufiv, save_board_to_ufiv

__all__ = ["load_board_from_ufiv",
           "save_board_to_ufiv"]

__author__ = "mihalin"
__email__ = "mihalin@physlab.ru"
