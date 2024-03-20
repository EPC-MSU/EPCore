"""
EyePoint module for basic PCB and measurements objects.

There is an object hierarchy:

- Board
  - Element
    - Pin
      - Measurement
        - MeasurementSettings
        - IVCurve

Upper objects (starting from board) can contain lower elements
(some elements can be empty). Lower elements should be completely
independent from upper elements. For example pin shouldn’t use
any Element methods and shouldn’t know about such objects.

To run example:
cd <to root epcore directory>
python -m epcore.elements

To build documentaion:
pydoc -w epcore.elements

To run tests:
python -m unittest discover epcore/elements
"""

from .board import Board, ImageNotFoundError, version
from .element import Element
from .measurement import IVCurve, Measurement, MeasurementSettings
from .pcbinfo import PCBInfo
from .pin import MultiplexerOutput, Pin


__all__ = ["Board", "Element", "ImageNotFoundError", "IVCurve", "Measurement", "MeasurementSettings",
           "MultiplexerOutput", "PCBInfo", "Pin", "version"]
__author__ = "mihalin"
__email__ = "mihalin@physlab.ru"
