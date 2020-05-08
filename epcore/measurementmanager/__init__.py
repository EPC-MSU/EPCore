"""
Measurement manager – module for managing a set of IVmeasurers
and making complex measurements (measurement plans).

To run example:
python -m epcore.measurementmanager
"""

from .measurementplan import MeasurementPlan
from .measurementsystem import MeasurementSystem

__all__ = ["MeasurementPlan", "MeasurementSystem"]

__author__ = ""
__email__ = ""
