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
    print(initial_settings.max_voltage, initial_settings.internal_resistance, initial_settings.probe_signal_frequency)

    # Search optimal settings
    # Avalailable:
    # - probe_signal_frequency = 10, 100, 1000, 10000
    # - internal_resistance = 475.0, 4750.0, 47500.0
    # - max_voltage = 1.2, 3.0, 5.0, 12.0   WARNING: don't forget zeros...

    for i in range(ITER):
        # first iteration -- gather data
        if i == 0:
            optimal_settings = MeasurementSettings(
                sampling_rate=10000,
                probe_signal_frequency=1000,
                internal_resistance=4750.0,
                max_voltage=12.0
            )
        # next iterations -- analyze data
        else:
            settings = measurer.get_settings()
            new_signal_frequency, new_internal_resistance, new_max_voltage = autosetup_settings(voltages, currents, settings)
            optimal_settings = MeasurementSettings(
                sampling_rate=10000,
                probe_signal_frequency=new_signal_frequency,
                internal_resistance = new_internal_resistance,
                max_voltage = new_max_voltage
            )

        print(optimal_settings)
        measurer.set_settings(optimal_settings)
        VC = measurer.measure_iv_curve()[0]
        voltages = VC.voltages
        currents = VC.currents

    # Set initial settings. Don't return without this!
    measurer.set_settings(initial_settings)

    return optimal_settings

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

def autosetup_settings(voltages, currents, settings):
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
    if c_avg < 0.2:
        if internal_resistance == 475.0:
            new_internal_resistance = 4750.0
        elif internal_resistance == 4750.0:
            new_internal_resistance = 47500.0
        else:
            new_internal_resistance = internal_resistance
    elif v_avg < 0.2:
        if internal_resistance == 47500.0:
            new_internal_resistance = 4750.0
        elif internal_resistance == 4750.0:
            new_internal_resistance = 475.0
        else:
            new_internal_resistance = internal_resistance
    else:
        new_internal_resistance = internal_resistance


    # change voltage
    new_max_voltage = 0
    for voltage in voltages:
        if abs(voltage) > new_max_voltage:
            new_max_voltage = abs(voltage)
    if new_max_voltage > 5.: new_max_voltage = 12
    elif new_max_voltage > 3.: new_max_voltage = 5
    elif new_max_voltage > 1.2: new_max_voltage = 3
    else: new_max_voltage = 1.2

    # change frequency
    # the thing is -- diod and capacitor have different behavior when changing frequency
    # possible bypass is storing past frequency and finding out whether area changes in direct ratio ot no
    # but this will do
    integral = integrate(voltages, currents)
    square = (max_voltage * 2) * (max_current * 2)
    print(f'integral {integral} square {square}')
    print("diff {}".format(abs(integral / square)))
    if (abs(integral / square) < 0.005) and (probe_signal_frequency > 10):
        new_signal_frequency = probe_signal_frequency / 10
    else:
        new_signal_frequency = probe_signal_frequency

    return new_max_voltage, new_internal_resistance, new_signal_frequency
