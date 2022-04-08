"""
Module to work with epmux multiplexer.

To run example in Windows:
cd <to root epcore directory>
python -m epcore.analogmultiplexer com:\\.\COMx

To run example in Linux:
cd <to root epcore directory>
python -m epcore.analogmutliplexer com:///dev/COMx

To build documentaion:
pydoc -w epcore.analogmultiplexer
"""

from .multiplexer import LineTypes, ModuleTypes, Multiplexer, MultiplexerIdentityInformation

__all__ = ["LineTypes", "ModuleTypes", "Multiplexer", "MultiplexerIdentityInformation"]
