from .product import EPLab
from ..measurementmanager import MeasurementSystem


if __name__ == "__main__":

    eplab = EPLab(MeasurementSystem())
    for name, parameter in eplab.get_all_available_options().items():
        print("Parameter: " + str(name) + " " + str(parameter))
