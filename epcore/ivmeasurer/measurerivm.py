"""
IVMeasurer Implementation for EyePoint IVM hardware measurer.
"""
from . import IVMeasurerIdentityInformation
from .base import IVMeasurerBase, cache_curve
from .ivm import IvmDeviceHandle
from ..elements import IVCurve, MeasurementSettings
import numpy as np


class IVMeasurerIVM10(IVMeasurerBase):
    """
    Class for controlling EyePoint IVM devices with
    API version 1.0.
    All instances should be initialized with device URL.
    Format for Windows: com:\\\\.\\COMx
    Format for Linux: /dev/ttyACMx
    """
    def __init__(self, url: str = ""):
        self._device = IvmDeviceHandle(url)
        self._FRAME_SIZE = 25
        default_settings = MeasurementSettings(
            sampling_rate=10000,
            internal_resistance=475,
            max_voltage=5,
            probe_signal_frequency=100,
            precharge_delay=0
        )
        self.set_settings(default_settings)
        super(IVMeasurerIVM10, self).__init__(url)

    def set_settings(self, settings: MeasurementSettings):
        device_settings = self._device.get_measurement_settings()

        if ((int(settings.sampling_rate) < 100) or
           (int(settings.sampling_rate) > 2000000)):
            raise ValueError("Invalid value for sampling rate: {}. Should be in [100, 2000000]".format(
                    settings.sampling_rate
                ))
        device_settings.sampling_rate = settings.sampling_rate
        device_settings.max_voltage = settings.max_voltage
        device_settings.probe_signal_frequency = settings.probe_signal_frequency

        if ((int(device_settings.probe_signal_frequency) < 1) or
           (int(device_settings.probe_signal_frequency) > 100000) or
           (int(device_settings.probe_signal_frequency) > device_settings.sampling_rate / 5)):
            raise ValueError("Invalid value for probe signal frequency: {}. Should be in [1, 100000]\
                             and also should be much less than sampling rate.".format(
                    device_settings.probe_signal_frequency
                ))

        # Choose one of available current sense resistors.
        if int(settings.internal_resistance) == 475:
            device_settings.current_sensor_mode = device_settings.current_sensor_mode.CURRENT_SENSE_MODE_I_HIGH
        elif int(settings.internal_resistance) == 4750:
            device_settings.current_sensor_mode = device_settings.current_sensor_mode.CURRENT_SENSE_MODE_I_MID
        elif int(settings.internal_resistance) == 47500:
            device_settings.current_sensor_mode = device_settings.current_sensor_mode.CURRENT_SENSE_MODE_I_LOW
        else:
            msg = "EyePoint IVM measurer has only three internal resistances: \
                   475 Ohm, 4750 Ohm and 47500 Ohm. Got internal resistance {} Ohm.".format(
                       settings.internal_resistance
                  )
            raise ValueError(msg)

        # We want only single sine period
        device_settings.number_points = int(settings.sampling_rate // settings.probe_signal_frequency)
        if settings.precharge_delay is not None:
            device_settings.number_charge_points = settings.precharge_delay * settings.sampling_rate
        else:
            device_settings.number_charge_points = 0
        device_settings.output_mode = device_settings.output_mode.OUT_MODE_PROBE_SIGNAL_CONTINUOUS
        self._device.set_measurement_settings(device_settings)

    def get_settings(self) -> MeasurementSettings:
        device_settings = self._device.get_measurement_settings()

        if device_settings.current_sensor_mode == device_settings.current_sensor_mode.CURRENT_SENSE_MODE_I_HIGH:
            internal_resistance = 475.
        elif device_settings.current_sensor_mode == device_settings.current_sensor_mode.CURRENT_SENSE_MODE_I_MID:
            internal_resistance = 4750.
        elif device_settings.current_sensor_mode == device_settings.current_sensor_mode.CURRENT_SENSE_MODE_I_LOW:
            internal_resistance = 47500.
        else:
            raise ValueError("Got unexpected current_sensor_mode from IVM Device: {}".format(
                device_settings.current_sensor_mode
            ))

        precharge_delay = device_settings.number_charge_points / device_settings.sampling_rate
        if int(precharge_delay) == 0:
            precharge_delay = None

        return MeasurementSettings(sampling_rate=device_settings.sampling_rate,
                                   internal_resistance=internal_resistance,
                                   max_voltage=device_settings.max_voltage,
                                   probe_signal_frequency=device_settings.probe_signal_frequency,
                                   precharge_delay=precharge_delay)

    def get_identity_information(self) -> IVMeasurerIdentityInformation:
        inf = self._device.get_identity_information()
        return IVMeasurerIdentityInformation(manufacturer=bytes(inf.manufacturer).decode("utf-8").replace("\x00", ""),
                                             device_name=bytes(inf.controller_name).decode("utf-8").replace("\x00", ""),
                                             device_class=bytes(inf.product_name).decode("utf-8").replace("\x00", ""),
                                             hardware_version=(inf.hardware_major, inf.hardware_minor,
                                                               inf.hardware_bugfix),
                                             firmware_version=(inf.firmware_major, inf.firmware_minor,
                                                               inf.firmware_bugfix),
                                             name=bytes(inf.controller_name).decode("utf-8").replace("\x00", ""))

    def trigger_measurement(self):
        if not self.is_freezed():
            self._device.start_measurement()

    def measurement_is_ready(self) -> bool:
        if self.is_freezed():
            return False

        return bool(self._device.check_measurement_status().ready_status.measurement_complete)

    @cache_curve
    def get_last_iv_curve(self) -> IVCurve:
        device_settings = self._device.get_measurement_settings()
        voltages = []
        currents = []
        for frame_number in range((device_settings.number_points - 1) // self._FRAME_SIZE + 1):
            frame = self._device.get_measurement(frame_number)
            currents.extend(list(frame.current))
            voltages.extend(list(frame.voltage))

        # Device return currents in mA
        currents = (np.array(currents[:device_settings.number_points]) / 1000).tolist()
        voltages = voltages[:device_settings.number_points]

        return IVCurve(
            currents=currents,
            voltages=voltages
        )
