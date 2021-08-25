"""
EyePoint module, which defines product functionality:
* number and types of devices;
* available modes;
* labels in GUI.
"""

from .product import (EPLab, InvalidJson, MeasurementParameter, MeasurementParameterOption,
                      ProductBase)

__all__ = ["EPLab",
           "InvalidJson",
           "MeasurementParameter",
           "MeasurementParameterOption",
           "ProductBase"]

__author__ = "mihalin"
__email__ = "mihalin@physlab.ru"
