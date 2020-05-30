"""
EyePoint module for file IO operations.

To run example:
python -m epcore.filemanager

To build documentaion:
pydoc -w epcore.filemanager

To run tests:
python -m unittest discover epcore/filemanager
"""

from .ufiv import load_board_from_ufiv, save_board_to_ufiv, add_image_to_ufiv
from .screenshot import save_screenshot


__all__ = ["load_board_from_ufiv",
           "save_board_to_ufiv",
           "add_image_to_ufiv",
           "save_screenshot"]

__author__ = "mihalin"
__email__ = "mihalin@physlab.ru"
