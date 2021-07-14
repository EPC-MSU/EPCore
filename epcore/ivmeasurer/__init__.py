"""
There is an IVMeasurerBase class, which implements standard interface.
All other implementations should be derived from this class and should support this interface.
Some implementations has additional methods and data structures. But they should be use for special purposes.
The standard interface should be sufficient for performing basic measurements
(with default values for special settings).

Implementations in plan:
* IVMeasurerBase
* IVMeasurerVirtual - Virtual measurer. You can use it without any hardware.
* IVMeasurerIVM10
* IVMeasurerNetClient

To run example:
cd <to root epcore directory>
python -m epcore.ivmeasurer

Virtual measurer is used by default.
To run example with real device set device url through –p argument:
python -m epcore.ivmeasurer -p com:\\\\.\\COM28

To build documentaion:
pydoc -w epcore.ivmeasurer

"""

from .base import IVMeasurerBase, IVMeasurerIdentityInformation
from .virtual import IVMeasurerVirtual
from .virtualbad import IVMeasurerVirtualBad
from .measurerivm import IVMeasurerIVM02, IVMeasurerIVM10

__all__ = ["IVMeasurerBase",
           "IVMeasurerVirtual",
           "IVMeasurerVirtualBad",
           "IVMeasurerIVM02",
           "IVMeasurerIVM10",
           "IVMeasurerIdentityInformation"]

__author__ = ""
__email__ = ""
