import logging
from .measurementplan import MeasurementPlan
from .measurementsystem import MeasurementSystem

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    logging.debug("Measurement manager example")

    mp = MeasurementPlan()
    mm = MeasurementSystem()
