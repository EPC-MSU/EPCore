"""
There is an IVMeasurerBase class, which implements standard interface. All
other implementations should be derived from this class and should support
this interface. Some implementations has additional methods and data
structures. But they should be used for special purposes. The standard
interface should be sufficient for performing basic measurements (with default
values for special settings).

Implementations in plan:
* IVMeasurerBase
* IVMeasurerVirtual - Virtual measurer. You can use it without any hardware.
* IVMeasurerIVM10
* IVMeasurerNetClient

To run example:
cd <to root epcore directory>
python -m epcore.ivmeasurer

Virtual measurer is used by default. To run example with real device set device
url through –p argument:
python -m epcore.ivmeasurer -p com:\\\\.\\COM28

To build documentaion:
pydoc -w epcore.ivmeasurer
"""

from .base import IVMeasurerBase, IVMeasurerIdentityInformation
from .measurerasa import IVMeasurerASA
from .measurerivm import IVMeasurerIVM10
from .virtual import IVMeasurerVirtual
from .virtualbad import IVMeasurerVirtualBad

__all__ = ["IVMeasurerASA",
           "IVMeasurerBase",
           "IVMeasurerIdentityInformation",
           "IVMeasurerIVM10",
           "IVMeasurerVirtual",
           "IVMeasurerVirtualBad"]

__author__ = ""
__email__ = ""
