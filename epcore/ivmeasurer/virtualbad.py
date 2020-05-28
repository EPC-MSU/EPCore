from .virtual import IVMeasurerVirtual
from random import random
from .base import IVMeasurerIdentityInformation
from ..elements import MeasurementSettings, IVCurve


class IVMeasurerVirtualBad(IVMeasurerVirtual):
    """
    Bad IVC Virtual Measurer with obvious connectivity issues
    """
    def __init__(self, url: str = "", name: str = "", fail_chance: float = 0.01):
        """
        :param url: url for device identification in computer system.
        For serial devices url will be "com:\\\\.\\COMx" (for Windows)
        or "com:///dev/tty/ttyACMx"
        :param name: friendly name (for measurement system)
        :param fail_chance: how bad is that measurer (0 - good, 1 - each command will fail)
        """
        self._fail_chance = fail_chance
        super(IVMeasurerVirtualBad, self).__init__(url, name)

        self._failed = False

    def _random_fail(self):
        if random() < self._fail_chance:
            self._failed = True  # Oops
        if self._failed:
            raise RuntimeError()

    def reconnect(self) -> bool:
        if random() < 0.8:
            self._failed = False  # Reboot heals everything
        return super(IVMeasurerVirtualBad, self).reconnect() and not self._failed

    # Add fail chance to every virtual measurer method
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
