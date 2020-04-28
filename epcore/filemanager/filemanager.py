from typing import List
from ..pin import Pin  # or: from epcore.pin import Pin (if epcore is in PYTHONPATH variable)


def save(pins: List[Pin]):
    for pin in pins:
        print("save " + str(pin.x))
