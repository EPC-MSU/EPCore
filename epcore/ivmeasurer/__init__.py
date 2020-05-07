"""
There is an IVMeasurerBase class, which implements standard interface. All other implementations should be derived from this class and should support this interface.
Some implementations has additional methods and data structures. But they should be use for special purposes. The standard interface should be sufficient for performing basic measurements (with default values for special settings).

Implementations in plan:
* IVMeasurerBase
* IVMeasurerVirtual - Virtual measurer. You can use it without any hardware.
* IVMeasurerIVM03
* IVMeasurerNetClient

To run example:
cd <to root epcore directory>
python -m epcore.ivmeasurer

To build documentaion:
pydoc -w epcore.ivmeasurer

"""

from .base import IVMeasurerBase, IVMeasurerIdentityInformation
from .virtual import IVMeasurerVirtual

__all__ = ["IVMeasurerBase",
           "IVMeasurerVirtual",
           "IVMeasurerIdentityInformation"]

__author__ = ""
__email__ = ""
