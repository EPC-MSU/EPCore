"""
EyePoint module for basic PCB and measurements objects.

There is an object hierarchy:

- Board
  - Element
    - Pin
      - Measurement
        - MeasurementSettings
        - IVCurve
        - [Point] array

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
pytest epcore/elements/tests/*.py
"""

from .measurement import Measurement, MeasurementSettings, Point
from .pin import Pin
from .element import Element
from .board import Board

__all__ = ["Point",
           "MeasurementSettings",
           "Measurement",
           "Pin",
           "Element",
           "Board"]

__author__ = "mihalin"
__email__ = "mihalin@pysabphyslab.ru"
