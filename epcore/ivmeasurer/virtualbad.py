from .virtual import IVMeasurerVirtual
from random import random
from .base import IVMeasurerIdentityInformation
from ..elements import MeasurementSettings, IVCurve


class IVMeasurerVirtualBad(IVMeasurerVirtual):
    """
    Bad IVC Virtual Measurer with obvious connectivity issues
    """
    def __init__(self, url: str = "", name: str = "", defer_open: bool = False, fail_chance: float = 0.01):
        """
        :param url: url for device identification in computer system.
        For serial devices url will be "com:\\\\.\\COMx" (for Windows)
        or "com:///dev/tty/ttyACMx"
        :param name: friendly name (for measurement system)
        :param defer_open: don't open serial port during initialization
        :param fail_chance: how bad is that measurer (0 - good, 1 - each command will fail)
        """
        self._fail_chance = fail_chance
        self._failed = False

        super(IVMeasurerVirtualBad, self).__init__(url, name, defer_open)

    def _random_fail(self):
        if random() < self._fail_chance:
            self._failed = True  # Oops
        if self._failed:
            raise RuntimeError()

    def reconnect(self) -> bool:
        self._failed = False
        try:
            self._failed = not super(IVMeasurerVirtualBad, self).reconnect()
        except RuntimeError:
            self._failed = True
        return self._failed

    # Add fail chance to every virtual measurer method
    def open_device(self):
        super(IVMeasurerVirtualBad, self).open_device()
        self._random_fail()

    def set_settings(self, settings: MeasurementSettings):
        self._random_fail()
        super(IVMeasurerVirtualBad, self).set_settings(settings)

    def get_settings(self) -> MeasurementSettings:
        self._random_fail()
        return super(IVMeasurerVirtualBad, self).get_settings()

    def get_identity_information(self) -> IVMeasurerIdentityInformation:
        self._random_fail()
        return super(IVMeasurerVirtualBad, self).get_identity_information()

    def trigger_measurement(self):
        self._random_fail()
        super(IVMeasurerVirtualBad, self).trigger_measurement()

    def measurement_is_ready(self) -> bool:
        self._random_fail()
        return super(IVMeasurerVirtualBad, self).measurement_is_ready()

    def get_last_iv_curve(self) -> IVCurve:
        self._random_fail()
        return super(IVMeasurerVirtualBad, self).get_last_iv_curve()

    def calibrate(self, *args):
        self._random_fail()
        super(IVMeasurerVirtualBad, self).calibrate()
