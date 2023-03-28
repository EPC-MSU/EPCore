from random import random
from epcore.elements import IVCurve, MeasurementSettings
from epcore.ivmeasurer.base import IVMeasurerIdentityInformation
from epcore.ivmeasurer.virtual import IVMeasurerVirtual


class IVMeasurerVirtualBad(IVMeasurerVirtual):
    """
    Bad virtual IV measurer with obvious connectivity issues.
    """

    def __init__(self, url: str = "", name: str = "", defer_open: bool = False, fail_chance: float = 0.01) -> None:
        """
        :param url: url for device identification in computer system.
        For serial devices url will be "com:\\\\.\\COMx" (for Windows) or "com:///dev/tty/ttyACMx" (for Linux);
        :param name: friendly name (for measurement system);
        :param defer_open: don't open serial port during initialization;
        :param fail_chance: how bad is that measurer (0 - good, 1 - each command will fail).
        """

        self._fail_chance: float = fail_chance
        self._failed: bool = False
        super().__init__(url, name, defer_open)

    def _random_fail(self) -> None:
        if random() < self._fail_chance:
            self._failed = True  # Oops
        if self._failed:
            raise RuntimeError()

    # Add fail chance to every virtual measurer method
    def calibrate(self, *args) -> None:
        self._random_fail()
        super().calibrate()

    def get_identity_information(self) -> IVMeasurerIdentityInformation:
        self._random_fail()
        return super().get_identity_information()

    def get_last_iv_curve(self) -> IVCurve:
        self._random_fail()
        return super().get_last_iv_curve()

    def get_settings(self) -> MeasurementSettings:
        self._random_fail()
        return super().get_settings()

    def measurement_is_ready(self) -> bool:
        self._random_fail()
        return super().measurement_is_ready()

    def reconnect(self) -> bool:
        self._failed = False
        try:
            self._failed = not super().reconnect()
        except RuntimeError:
            self._failed = True
        return not self._failed

    def set_settings(self, settings: MeasurementSettings = None) -> None:
        self._random_fail()
        super().set_settings(settings)

    def trigger_measurement(self) -> None:
        self._random_fail()
        super().trigger_measurement()
