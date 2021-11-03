"""
EyePoint module, which defines product functionality:
* number and types of devices;
* available modes;
* labels in GUI.
"""

from .product import (EyePointProduct, InvalidJson, MeasurementParameter, MeasurementParameterOption,
                      ProductBase)

__all__ = ["EyePointProduct",
           "InvalidJson",
           "MeasurementParameter",
           "MeasurementParameterOption",
           "ProductBase"]

__author__ = "mihalin"
__email__ = "mihalin@physlab.ru"
