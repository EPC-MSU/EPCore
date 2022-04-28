"""
Module to work with epmux multiplexer.

To run example in Windows:
cd <to root epcore directory>
python -m epcore.analogmultiplexer com:\\\\.\\COMx

To run example in Linux:
cd <to root epcore directory>
python -m epcore.analogmutliplexer com:///dev/ttyACMx

To build documentaion:
pydoc -w epcore.analogmultiplexer
"""

from .base import (AnalogMultiplexerBase, BadMultiplexerOutputError, LineTypes, ModuleTypes,
                   MultiplexerIdentityInformation)
from .multiplexer import AnalogMultiplexer
from .virtual import AnalogMultiplexerVirtual

__all__ = ["AnalogMultiplexer", "AnalogMultiplexerBase", "AnalogMultiplexerVirtual", "BadMultiplexerOutputError",
           "LineTypes", "ModuleTypes", "MultiplexerIdentityInformation"]
