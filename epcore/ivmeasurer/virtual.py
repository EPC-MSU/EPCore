import logging
import time
import numpy as np

from .base import IVMeasurerBase, IVMeasurerIdentityInformation
from ..elements import MeasurementSettings, IVCurve

class IVMeasurerVirtual():
    """
    Base class, which implements standard interface for 
    all IVMeasurers
    """
    logging.debug("IVMeasurerVirtual created")
    def __init__(self, url: str = "") -> "IVMeasurerVirtual":
        """
        :param url: url for device identification in computer system.
        For serial devices url will be "com:\\\\.\\COMx" (for Windows)
        or "com:///dev/tty/ttyACMx" 
        """
        self.url = url
        self.__settings = MeasurementSettings(
            sampling_rate=10000,
            internal_resistance=475.,
            max_voltage=12.,
            probe_signal_frequency=100
        )
        self.__last_curve = IVCurve()
        self.__measurement_is_ready = False
        self.phase = 0
        self.model = "resistor"
        self.nominal = 100

    def set_settings(self, settings: MeasurementSettings):
        self.__settings = settings

    def get_settings(self) -> MeasurementSettings:
        return self.__settings

    def get_identity_information(self) -> IVMeasurerIdentityInformation:
        return IVMeasurerIdentityInformation(
                manufacturer = "EPC MSU",
                device_class = "EyePoint virtual device",
                device_name = "Virtual IV Measurer",
                hardware_version = (0, 0, 0),
                firmware_version = (0, 0, 0),
                name = "Virtual"
        )

    def trigger_measurement(self):
        """
        Trigger measurement manually. 
        You don’t need this if the hardware is in continuous mode.
        """
        self.__measurement_is_ready = False
        if self.model == "resistor":
            self.__last_curve = self.__calculate_r_iv()
        elif self.model == "capacitor":
            self.__last_curve = self.__calculate_c_iv()
        else:
            raise NotImplementedError

        self.__measurement_is_ready = True

    def measurement_is_ready(self) -> bool:
        """
        Return true if new measurement is ready
        """
        return self.__measurement_is_ready

    def get_last_iv_curve(self) -> IVCurve:
        """
        Return result of the last measurement.
        """
        if self.__measurement_is_ready:
            return self.__last_curve
        else:
            raise RuntimeError("Measurement is not ready")

    def measure_iv_curve(self) -> IVCurve:
        """
        Perform measurement and return result for the measurement, which was made.
        Blocking function. May take some time.
        """
        self.trigger_measurement()
        # In ideal case it should be 1, 
        # but we set 5 to consider worst case
        self.__measurement_is_ready = False
        time.sleep(5. / (2 * np.pi * self.__settings.probe_signal_frequency))
        self.__measurement_is_ready = True

        return self.get_last_iv_curve()

    # =================== Internal methods =================================
    def __calculate_r_iv(self) -> IVCurve:
        """
        This function calculated current and
        voltage with generated settings with resistor
        """
        n_points = self.__settings.sampling_rate // self.__settings.probe_signal_frequency
        t = np.linspace(0, 1. / (2 * np.pi * self.__settings.probe_signal_frequency), n_points)

        v_in = self.__settings.max_voltage * np.sin(self.phase + 2 * np.pi * t / t[n_points - 1])

        #                  R
        # V_out = V_in ---------; R - model of connected resistor under test.
        #               R + R_cs
        v_out = v_in * self.nominal / (self.nominal + self.__settings.internal_resistance)
        # I_out = V_out / R
        i_out = v_out / self.nominal

        return IVCurve(
            currents=i_out.tolist(),
            voltages=v_out.tolist()
        )
        

    def __calculate_c_iv(self):
        """
        This function calculated current and
        voltage with generated settings with capacitor
        :return: array of current and voltage

        """
        n_points = self.__settings.sampling_rate // self.__settings.probe_signal_frequency
        r_lim = self.__settings.internal_resistance
        phase = self.phase
        t = np.linspace(0, 1. / (2 * np.pi * self.__settings.probe_signal_frequency), n_points)
        v_in = self.__settings.max_voltage * np.sin(phase + 2 * np.pi * t / t[n_points - 1])

        v_out = np.zeros(n_points)
        i_out = np.zeros(n_points)

        for i in range(1, n_points):
            v_out[i] = (v_out[i - 1] - v_in[i - 1]) * np.exp(-(t[i] - t[i - 1]) /
                                                            (self.nominal * r_lim))
            v_out[i] += v_in[i - 1] # <----- Check this
            i_out[i] = (v_in[i] - v_out[i]) / r_lim

        return IVCurve(
            currents=i_out.tolist(),
            voltages=v_out.tolist()
        )
