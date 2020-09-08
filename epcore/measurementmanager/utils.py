"""
Auxiliary functions for measurements
"""

from ..elements import MeasurementSettings
from ..ivmeasurer import IVMeasurerBase
import numpy as np
from scipy import interpolate

ITER = 3


def search_optimal_settings(measurer: IVMeasurerBase) -> MeasurementSettings:
    """
    Experimental search for optimal settings for specified IVMeasurer.
    During the search IVMeasurer should be connected to a testing component.
    IVCurve with the optimal settings will have the most meaningful form.
    For example for a capacitor it should be ellipse.
    Warning! During the search a set of measurements with various settings will be performed.
    To avoid damage don’t use this function for sensitive components.
    """
    # Save initial settings. At the end we will set measurer to initial state
    initial_settings = measurer.get_settings()
    maximize_square = True  # if true then area under the curve will be maximized even for diodes and resistors

    # Search optimal settings
    # TODO: find a way to get avalailable options
    # Avalailable:
    # - probe_signal_frequency = 10, 100, 1000, 10000, 100000
    # - sampling_rate = 1000, 10000, 100000, 1000000, 2000000 (according to probe_sample_frequency)
    # - internal_resistance = 475.0, 4750.0, 47500.0
    # - max_voltage = 1.2, 3.0, 5.0, 12.0
    optimal_settings = MeasurementSettings(
        sampling_rate=1000000,
        probe_signal_frequency=10000,
        internal_resistance=4750.0,
        max_voltage=12.0
    )
    integral = []
    measurer.set_settings(optimal_settings)
    VC = measurer.measure_iv_curve()
    voltages = VC.voltages
    currents = VC.currents
    for i in range(1, ITER):
        settings = measurer.get_settings()
        (new_sampling_rate, new_signal_frequency,
         new_internal_resistance, new_max_voltage) = autosetup_settings(voltages, currents,
                                                                        integral, maximize_square, settings)
        optimal_settings = MeasurementSettings(
            sampling_rate=new_sampling_rate,
            probe_signal_frequency=new_signal_frequency,
            internal_resistance=new_internal_resistance,
            max_voltage=new_max_voltage
        )
        measurer.set_settings(optimal_settings)
        VC = measurer.measure_iv_curve()
        voltages = VC.voltages
        currents = VC.currents

    # Set initial settings. Don't return without this!
    measurer.set_settings(initial_settings)

    return optimal_settings


def autosetup_settings(voltages, currents, integral, maximize_square, settings):
    # get current settings
    probe_signal_frequency = settings.probe_signal_frequency
    internal_resistance = settings.internal_resistance
    max_voltage = settings.max_voltage
    max_current = max_voltage / internal_resistance

    # change current
    c_avg = np.mean(np.abs(currents))
    v_avg = np.mean(np.abs(voltages))
    c_avg /= max_current
    v_avg /= max_voltage
    if c_avg < 0.15 and internal_resistance < 47500.0:
        new_internal_resistance = internal_resistance * 10
    elif v_avg < 0.15 and internal_resistance > 475.0:
        new_internal_resistance = internal_resistance / 10
    else:
        new_internal_resistance = internal_resistance

    # change voltage
    new_max_voltage = 0
    for voltage in voltages:
        if abs(voltage) > new_max_voltage:
            new_max_voltage = abs(voltage)
    if new_max_voltage > 5.0:
        new_max_voltage = 12.0
    elif new_max_voltage > 3.3:
        new_max_voltage = 5.0
    elif new_max_voltage > 1.2:
        new_max_voltage = 3.3
    else:
        new_max_voltage = 1.2

    # change frequency algoritm for ITER = 3
    square = (max_voltage * 2) * (max_current * 2)
    integral.append(abs(integrate(voltages, currents) / square))
    if maximize_square:
        # first check is made to be certain that 10KHz is not optimal
        if (integral[0] < 0.003) and (probe_signal_frequency > 10) and (len(integral) == 1):
            new_signal_frequency = probe_signal_frequency / 100
        # if it is optimal then keep the frequency (mostly optimal for diodes)
        elif len(integral) == 1:
            new_signal_frequency = probe_signal_frequency
        # second check is to determine whether frequency changes in direct ratio with integral or not
        elif ((integral[1] / integral[0]) > 1.2) and (probe_signal_frequency > 10):
            new_signal_frequency = probe_signal_frequency / 10
        elif ((integral[1] / integral[0]) < 1) and (probe_signal_frequency < 10000):
            new_signal_frequency = probe_signal_frequency * 100
        else:
            new_signal_frequency = probe_signal_frequency
    else:
        if (integral[-1] < 0.05) and (probe_signal_frequency > 10):
            new_signal_frequency = probe_signal_frequency / 10
        else:
            new_signal_frequency = probe_signal_frequency

    # choose sampling rate accordingly
    if new_signal_frequency != 100000:
        new_sampling_rate = new_signal_frequency * 100
    else:
        new_sampling_rate = 2000000

    return new_sampling_rate, new_signal_frequency, new_internal_resistance, new_max_voltage


def _equidistant(voltages, currents):
    # there are some repeats...
    an = np.array([voltages, currents])
    params = np.arange(0, 1, 1.0 / len(an[0]))
    step = 1.0 / len(an[0])
    tck, _ = interpolate.splprep(an, u=params, s=0.00)
    eq = np.array(interpolate.splev(params, tck))
    return eq, step


def integrate(voltages, currents):
    eq, step = _equidistant(voltages, currents)
    integral = 0.0
    for i in range(len(eq[1])-1):
        integral += step * (eq[1][i] + eq[1][i+1]) / 2
    # np.trapz works literally the same
    return integral
