"""
IVMeasurer Implementation for EyePoint IVM hardware measurer.
"""
from . import IVMeasurerIdentityInformation
from .base import IVMeasurerBase
from .ivm import IvmDeviceHandle
from ..elements import IVCurve, MeasurementSettings


class IVMeasurerIVM03(IVMeasurerBase):

    def __init__(self, url: str = ""):
        self._device = IvmDeviceHandle(url)
        super(IVMeasurerIVM03, self).__init__(url)

    def set_settings(self, settings: MeasurementSettings):
        device_settings = self._device.get_measurement_settings()
        device_settings.sampling_rate = settings.sampling_rate
        device_settings.max_voltage = settings.max_voltage
        device_settings.probe_signal_frequency = settings.probe_signal_frequency
        # TODO: internal_resistance, max_voltage ?
        self._device.set_measurement_settings(device_settings)

    def get_settings(self) -> MeasurementSettings:
        device_settings = self._device.get_measurement_settings()
        return MeasurementSettings(sampling_rate=device_settings.sampling_rate,
                                   internal_resistance=0,  # TODO: this
                                   max_voltage=device_settings.max_voltage,
                                   probe_signal_frequency=device_settings.probe_signal_frequency,
                                   precharge_delay=None)  # TODO: this

    def get_identity_information(self) -> IVMeasurerIdentityInformation:
        inf = self._device.get_identity_information()
        return IVMeasurerIdentityInformation(manufacturer=inf.manufacturer,
                                             device_name=inf.controller_name,  # TODO: device name?
                                             device_class=inf.product_name,    # TODO: device class?
                                             hardware_version=(inf.hardware_major, inf.hardware_minor,
                                                               inf.hardware_bugfix),
                                             firmware_version=(inf.firmware_major, inf.firmware_minor,
                                                               inf.firmware_bugfix),
                                             name=inf.controller_name)

    def trigger_measurement(self):
        self._device.start_measurement()

    def measurement_is_ready(self) -> bool:
        return bool(self._device.check_measurement_status().ready_status.measurement_complete)

    def get_last_iv_curve(self) -> IVCurve:
        return IVCurve()  # TODO: how to get last frame?
