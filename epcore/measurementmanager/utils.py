"""
Auxiliary functions for measurements
"""

from ..elements import MeasurementSettings
from ..ivmeasurer import IVMeasurerBase


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

    # Search optimal settings
    optimal_settings = MeasurementSettings(
        sampling_rate=10000,
        probe_signal_frequency=100,
        internal_resistance=475,
        max_voltage=5
    )
    measurer.set_settings(optimal_settings)

    # Set initial settings. Don't return without this!
    measurer.set_settings(initial_settings)

    return optimal_settings
