"""
File with an example of working with Meridian device using MdasaMeasurer.
"""

from .elements import MeasurementSettings
from .measurer import MdasaMeasurer

if __name__ == "__main__":

    settings = MeasurementSettings(
        sampling_rate=1000.,
        probe_signal_frequency=10.,
        max_voltage=2.,
        max_current=1.,
        n_points=512,
        n_charge_points=400,
        flags=3,
        model_type="",
        model_nominal=0,
        mode="Auto")
    measurer = MdasaMeasurer("xmlrpc:172.16.3.213", "mdasa_measurer", True)
    measurer.set_host()
    measurer.set_settings(**settings.to_json())
    print(measurer.get_settings())
