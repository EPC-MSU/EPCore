import logging
import time
import numpy as np

from .base import IVMeasurerBase, IVMeasurerIdentityInformation, cache_curve
from ..elements import MeasurementSettings, IVCurve


class IVMeasurerVirtual(IVMeasurerBase):
    """
    Virtual IVMeasurer
    """
    def __init__(self, url: str = ""):
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
        self.__ready_time = 0
        self.__measurement_is_ready = False
        self.phase = 0
        self.model = "resistor"
        self.nominal = 100
        self.noise_factor = 0.05
        logging.debug("IVMeasurerVirtual created")
        super(IVMeasurerVirtual, self).__init__(url)

    def set_settings(self, settings: MeasurementSettings):
        self.__settings = settings

    def get_settings(self) -> MeasurementSettings:
        return self.__settings

    def get_identity_information(self) -> IVMeasurerIdentityInformation:
        return IVMeasurerIdentityInformation(
                manufacturer="EPC MSU",
                device_class="EyePoint virtual device",
                device_name="Virtual IV Measurer",
                hardware_version=(0, 0, 0),
                firmware_version=(0, 0, 0),
                name="Virtual"
        )

    def trigger_measurement(self):
        """
        Trigger measurement manually.
        You don’t need this if the hardware is in continuous mode.
        """

        if self.is_freezed():
            return

        self.__measurement_is_ready = False
        if self.model == "resistor":
            self.__last_curve = self.__calculate_r_iv()
        elif self.model == "capacitor":
            self.__last_curve = self.__calculate_c_iv()
        else:
            raise NotImplementedError
        self.__measurement_is_ready = False
        self.__ready_time = time.time() + 2. / self.__settings.probe_signal_frequency

    def measurement_is_ready(self) -> bool:
        """
        Return true if new measurement is ready
        """
        if self.is_freezed():
            return False

        if time.time() > self.__ready_time:
            self.__measurement_is_ready = True

        return self.__measurement_is_ready

    @cache_curve
    def get_last_iv_curve(self) -> IVCurve:
        """
        Return result of the last measurement.
        """
        if self.__measurement_is_ready:
            return self.__last_curve
        else:
            raise RuntimeError("Measurement is not ready")

    def calibrate(self, *args):
        """
        We don't need to calibrate virtual IVC
        :param args:
        :return:
        """
        pass

    # =================== Internal methods =================================
    def __add_noise(self, voltages_arr, currents_arr):
        voltage_noise_ampl = self.__settings.max_voltage * self.noise_factor
        voltages_arr = np.array(voltages_arr) + voltage_noise_ampl * np.random.random(len(voltages_arr))

        current_noise_ampl = (self.__settings.max_voltage / (self.__settings.internal_resistance + 100) *
                              self.noise_factor)
        currents_arr = np.array(currents_arr) + current_noise_ampl * np.random.random(len(currents_arr))

        return (voltages_arr, currents_arr)

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

        v_out, i_out = self.__add_noise(v_out, i_out)

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
            v_out[i] = (v_out[i - 1] - v_in[i - 1]) * np.exp(-(t[i] - t[i - 1]) / (self.nominal * r_lim))
            v_out[i] += v_in[i - 1]  # <----- Check this
            i_out[i] = (v_in[i] - v_out[i]) / r_lim

        v_out, i_out = self.__add_noise(v_out, i_out)

        return IVCurve(
            currents=i_out.tolist(),
            voltages=v_out.tolist()
        )
