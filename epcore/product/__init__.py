"""
EyePoint module, which defines product functionality:
* number and types fo devices
* available modes
* labels in GUI
"""
from .product import ProductBase, EPLab, MeasurementParameter, MeasurementParameterOption

__all__ = ["MeasurementParameterOption",
           "MeasurementParameter",
           "ProductBase",
           "EPLab"]

__author__ = "mihalin"
__email__ = "mihalin@physlab.ru"
