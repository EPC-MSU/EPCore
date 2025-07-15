"""
IVMeasurer Implementation for EyePoint IVM hardware measurer.
"""

import logging
from typing import Tuple
import numpy as np
from ivm import IvmDeviceHandle
from ..elements import IVCurve, MeasurementSettings
from .ivmeasurerbase import cache_curve, close_on_error, IVMeasurerBase, IVMeasurerIdentityInformation
from .processing import interpolate_curve, smooth_curve
from .safe_opener import open_device_safe


_logger = logging.getLogger(__name__)


def _logging_callback(loglevel, message, user_data):
    if loglevel == 0x01:
        _logger.error(message)
    elif loglevel == 0x02:
        _logger.warning(message)
    elif loglevel == 0x03:
        _logger.info(message)
    elif loglevel == 0x04:
        _logger.debug(message)


class IVMeasurerIVM(IVMeasurerBase):
    """
    Class for controlling EyePoint IVM devices.
    """

    _FRAME_SIZE: int = 25
    _NORMAL_NUM_POINTS: int = 100
    _SMOOTHING_KERNEL_SIZE: int = 5

    def __init__(self, url: str = "", name: str = "", config: str = "", defer_open: bool = False,
                 force_open: bool = False) -> None:
        """
        :param url: url for device identification in computer system.
        For serial devices url will be "com:\\\\.\\COMx" (for Windows) or "com:///dev/ttyACMx" (for Linux);
        :param name: friendly name (for measurement system);
        :param config: path to config file;
        :param defer_open: don't open serial port during initialization;
        :param force_open: to check device compatibility device will be opened despite the errors
        (device will be closed after compatibility check).
        """

        super().__init__(url, name)
        self._config: str = config
        self._device: IvmDeviceHandle = IvmDeviceHandle(url, defer_open=True)
        self._default_settings: MeasurementSettings = MeasurementSettings(sampling_rate=10000,
                                                                          internal_resistance=4750,
                                                                          max_voltage=5,
                                                                          probe_signal_frequency=100,
                                                                          precharge_delay=0)
        open_device_safe(self._url, IvmDeviceHandle, self._config, _logging_callback, force_open)

        if not defer_open:
            self.open_device()

    @close_on_error
    def calibrate(self, *args) -> int:
        """
        :return: calibration result code.
        """

        # TODO: calibration settings?
        return self._device.start_autocalibration().result

    def close_device(self) -> None:
        try:
            self._device.close_device()
        except (RuntimeError, OSError):
            pass

    @close_on_error
    def get_button_events(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        :return: two tuples. The first tuple records events for buttons on the generator probe. The second tuple
        records events for buttons on the recv probe. In each tuple with events for buttons:
        * the first element records whether the button was pressed (if it was, then not 0);
        * the second element records whether the button was released (if it was, then not 0).
        """

        status = self._device.get_status()
        io_events = status.io_events
        gen_events = io_events.ioevents_gen_probe_button_pressed, io_events.ioevents_gen_probe_button_released
        recv_events = io_events.ioevents_recv_probe_button_pressed, io_events.ioevents_recv_probe_button_released
        return gen_events, recv_events

    @close_on_error
    def get_button_states(self) -> Tuple[int, int]:
        """
        :return: tuple with states of buttons on probes. The first element is responsible for the state of the button
        on the generator probe. The second element is responsible for the state of the button on the recv probe.
        If not 0, then the button is pressed.
        """

        status = self._device.get_status()
        io_state = status.io_state
        return io_state.iostate_gen_probe_button_pressed, io_state.iostate_recv_probe_button_pressed

    @close_on_error
    def get_identity_information(self) -> IVMeasurerIdentityInformation:
        """
        :return: main identity information about device.
        """

        info = self._device.get_identity_information()
        return IVMeasurerIdentityInformation(
            manufacturer=bytes(info.manufacturer).decode("utf-8").replace("\x00", ""),
            device_name=bytes(info.controller_name).decode("utf-8").replace("\x00", ""),
            device_class=bytes(info.product_name).decode("utf-8").replace("\x00", ""),
            hardware_version=(info.hardware_major, info.hardware_minor, info.hardware_bugfix),
            firmware_version=(info.firmware_major, info.firmware_minor, info.firmware_bugfix),
            name=bytes(info.controller_name).decode("utf-8").replace("\x00", ""))

    @cache_curve
    @close_on_error
    def get_last_iv_curve(self, raw: bool = False) -> IVCurve:
        """
        :param raw: if True then postprocessing (averaging) is not applied.
        :return: measured data from device.
        """

        device_settings = self._device.get_measurement_settings()
        voltages = []
        currents = []
        for frame_number in range((device_settings.number_points - 1) // IVMeasurerIVM._FRAME_SIZE + 1):
            frame = self._device.get_measurement(frame_number)
            currents.extend(list(frame.current))
            voltages.extend(list(frame.voltage))

        # Device return currents in mA
        currents = (np.array(currents[:device_settings.number_points]) / 1000).tolist()
        voltages = voltages[:device_settings.number_points]
        curve = IVCurve(currents=currents, voltages=voltages)

        if raw is True:
            return curve

        # Postprocessing
        if device_settings.probe_signal_frequency > 20000:
            curve = interpolate_curve(curve=curve, final_num_points=IVMeasurerIVM._NORMAL_NUM_POINTS)

        curve = smooth_curve(curve=curve, kernel_size=IVMeasurerIVM._SMOOTHING_KERNEL_SIZE)
        return curve

    @close_on_error
    def get_settings(self) -> MeasurementSettings:
        """
        :return: measurement settings set on the device.
        """

        device_settings = self._device.get_measurement_settings()

        if device_settings.current_sensor_mode == device_settings.current_sensor_mode.CURRENT_SENSE_MODE_I_HIGH:
            internal_resistance = 475.
        elif device_settings.current_sensor_mode == device_settings.current_sensor_mode.CURRENT_SENSE_MODE_I_MID:
            internal_resistance = 4750.
        elif device_settings.current_sensor_mode == device_settings.current_sensor_mode.CURRENT_SENSE_MODE_I_LOW:
            internal_resistance = 47500.
        else:
            raise ValueError("Got unexpected current_sensor_mode from IVM device: "
                             f"{device_settings.current_sensor_mode}.")

        precharge_delay = device_settings.number_charge_points / device_settings.sampling_rate
        if int(precharge_delay) == 0:
            precharge_delay = None

        return MeasurementSettings(sampling_rate=device_settings.sampling_rate,
                                   internal_resistance=internal_resistance,
                                   max_voltage=device_settings.max_voltage,
                                   probe_signal_frequency=device_settings.probe_signal_frequency,
                                   precharge_delay=precharge_delay)

    @close_on_error
    def measurement_is_ready(self) -> bool:
        """
        :return: True if new measurement is ready.
        """

        if self.is_freezed():
            return False

        return bool(self._device.check_measurement_status().ready_status.measurement_complete)

    @close_on_error
    def open_device(self) -> None:
        self._device.open_device()
        self.set_settings(self._default_settings)

    def reconnect(self) -> bool:
        """
        :return: True if the reconnect was successful.
        """

        self.close_device()
        try:
            self.open_device()
            return True
        except (RuntimeError, OSError):
            return False

    def reset_button_events(self) -> None:
        self._device.reset_events(15, 1)

    @close_on_error
    def set_settings(self, settings: MeasurementSettings = None) -> None:
        """
        :param settings: measurement settings to be set on device.
        """

        if settings is None:
            return

        device_settings = self._device.get_measurement_settings()
        if int(settings.sampling_rate) < 100 or int(settings.sampling_rate) > 2000000:
            raise ValueError(f"Invalid value for sampling rate: {settings.sampling_rate}. Should be in [100, 2000000].")

        device_settings.sampling_rate = settings.sampling_rate
        device_settings.max_voltage = settings.max_voltage
        device_settings.probe_signal_frequency = settings.probe_signal_frequency
        if (int(device_settings.probe_signal_frequency) < 1 or int(device_settings.probe_signal_frequency) > 100000 or
                int(device_settings.probe_signal_frequency) > device_settings.sampling_rate / 5):
            raise ValueError(f"Invalid value for probe signal frequency: {device_settings.probe_signal_frequency}. "
                             "Should be in [1, 100000] and also should be much less than sampling rate.")

        # Choose one of available current sense resistors.
        if int(settings.internal_resistance) == 475:
            device_settings.current_sensor_mode = device_settings.current_sensor_mode.CURRENT_SENSE_MODE_I_HIGH
        elif int(settings.internal_resistance) == 4750:
            device_settings.current_sensor_mode = device_settings.current_sensor_mode.CURRENT_SENSE_MODE_I_MID
        elif int(settings.internal_resistance) == 47500:
            device_settings.current_sensor_mode = device_settings.current_sensor_mode.CURRENT_SENSE_MODE_I_LOW
        else:
            raise ValueError("EyePoint IVM measurer has only three internal resistances: 475 Ohm, 4750 Ohm and "
                             f"47500 Ohm. Got internal resistance {settings.internal_resistance} Ohm.")

        # We want only single sine period
        device_settings.number_points = int(settings.sampling_rate // settings.probe_signal_frequency)
        if settings.precharge_delay is not None:
            device_settings.number_charge_points = int(settings.precharge_delay * settings.sampling_rate)
        else:
            device_settings.number_charge_points = 0
        device_settings.output_mode = device_settings.output_mode.OUT_MODE_PROBE_SIGNAL_CONTINUOUS
        self._device.set_measurement_settings(device_settings)

    @close_on_error
    def trigger_measurement(self) -> None:
        if not self.is_freezed():
            self._device.start_measurement()
