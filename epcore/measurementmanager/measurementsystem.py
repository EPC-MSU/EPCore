import time
from copy import deepcopy
from typing import Dict, List, Optional
import numpy as np
from epcore.analogmultiplexer import AnalogMultiplexerBase
from epcore.elements import IVCurve, MeasurementSettings, MultiplexerOutput
from epcore.ivmeasurer import IVMeasurerBase


class MeasurementSystem:
    """
    Provide mass operations with a number of IVMeasurers. If you have only
    single IVMeasurer, it is recommended to use this class for compatibility.
    """

    measurers: List[IVMeasurerBase]
    measurers_map: Dict[str, IVMeasurerBase]
    multiplexers: List[AnalogMultiplexerBase]

    def __init__(self, measurers: Optional[List[IVMeasurerBase]] = None,
                 multiplexers: Optional[List[AnalogMultiplexerBase]] = None):
        """
        :param measurers: measurers for measurement system;
        :param multiplexers: multiplexers for measurement system.
        """

        self.measurers = measurers or []
        # Two containers for the same thing is not a good feature.
        # Consider removing and try not to use this
        self.measurers_map = {measurer.name: measurer for measurer in self.measurers if measurer.name}
        self.multiplexers = multiplexers or []

    def calibrate(self):
        """
        Calibrate all measurers.
        """

        for measurer in self.measurers:
            measurer.calibrate()

    def get_settings(self) -> MeasurementSettings:
        """
        Check whether all measurers have the same settings.
        :return: settings if all measurers have the same. Else throw RuntimeError.
        """

        all_settings = [measurer.get_settings() for measurer in self.measurers]
        if not all_settings:
            raise ValueError("No ivc measurers")
        precision = 0.01
        s0 = all_settings[0]
        for s in all_settings:
            if (not np.isclose(s.internal_resistance, s0.internal_resistance, atol=precision) or
                    s.sampling_rate != s0.sampling_rate or
                    s.probe_signal_frequency != s0.probe_signal_frequency or
                    not np.isclose(s.max_voltage, s0.max_voltage, atol=precision)):
                raise ValueError("Settings are different for measurers")
        return deepcopy(all_settings[0])

    def has_active_analog_multiplexers(self) -> bool:
        """
        Check whether there are analog multiplexers in measurement system.
        :return: True if there are analog multiplexers.
        """

        return len(self.multiplexers) > 0

    def measure_iv_curves(self) -> List[IVCurve]:
        """
        Make measurements and get new curves from all devices.
        :return: list with IV-curves from measurers.
        """

        self.trigger_measurements()
        while not self.measurements_are_ready():
            time.sleep(0.05)
        return [measurer.get_last_iv_curve() for measurer in self.measurers]

    def measurements_are_ready(self) -> bool:
        """
        Return True if all measurers have done their job.
        :return: True if all measurers have done their job.
        """

        return all([measurer.measurement_is_ready() for measurer in self.measurers if not measurer.is_freezed()])

    def reconnect(self) -> bool:
        """
        Reconnect all measurers.
        :return: True if reconnection of all measurers was successful.
        """

        return all([device.reconnect() for device in [*self.measurers, *self.multiplexers]])

    def set_multiplexer_output(self, output: MultiplexerOutput):
        """
        Sets outputs for all multiplexers in measurement system.
        :param output: output to be set.
        """

        for multiplexer in self.multiplexers:
            multiplexer.connect_channel(output)

    def set_settings(self, settings: MeasurementSettings):
        """
        Assign same settings for all measurers.
        :param settings: settings to be set.
        """

        for measurer in self.measurers:
            measurer.set_settings(settings)

    def trigger_measurements(self):
        """
        Trigger measurements on all devices.
        """

        for measurer in self.measurers:
            measurer.trigger_measurement()

    def unfreeze(self):
        """
        Unfreeze all measurers.
        """

        for measurer in self.measurers:
            measurer.unfreeze()
