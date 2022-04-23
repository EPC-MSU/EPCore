from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .abstract import JsonConvertible


@dataclass
class MeasurementSettings(JsonConvertible):
    """
    Basic settings for IV-curve measurement.
    """

    sampling_rate: int
    internal_resistance: float
    max_voltage: float
    probe_signal_frequency: int
    precharge_delay: Optional[float] = None

    def __post_init__(self):
        # Current EPCore version supports only integer rate\freq
        self.sampling_rate = int(self.sampling_rate)
        self.probe_signal_frequency = int(self.probe_signal_frequency)

    @classmethod
    def create_from_json(cls, json_data: Dict) -> "MeasurementSettings":
        """
        Create object from dict with structure compatible with UFIV JSON file schema.
        :param json_data: dict with information.
        :return: object.
        """

        return MeasurementSettings(
            sampling_rate=json_data["sampling_rate"],
            internal_resistance=json_data["internal_resistance"],
            max_voltage=json_data["max_voltage"],
            probe_signal_frequency=json_data["probe_signal_frequency"],
            precharge_delay=json_data.get("precharge_delay")
        )

    def to_json(self) -> Dict:
        """
        Return dict with structure compatible with UFIV JSON file schema.
        :return: dict with information about object.
        """

        json_data = {
            "sampling_rate": self.sampling_rate,
            "internal_resistance": self.internal_resistance,
            "max_voltage": self.max_voltage,
            "probe_signal_frequency": self.probe_signal_frequency,
            "precharge_delay": self.precharge_delay
        }
        return self.remove_unused(json_data)


@dataclass
class IVCurve(JsonConvertible):
    """
    IVCurve data. Measurement results only.
    """

    currents: List[float] = field(default_factory=lambda: [0., 0.])
    voltages: List[float] = field(default_factory=lambda: [0., 0.])

    def __post_init__(self):
        n_currents = len(self.currents)
        n_voltages = len(self.voltages)
        if n_currents != n_voltages:
            raise ValueError("Currents and voltages array lengths should be equal. Got len(currents) = {},"
                             " len(voltages) = {}".format(n_currents, n_voltages))
        if n_currents < 2:
            raise ValueError("IV curve should contain at least 2 points for correct operation, "
                             "got {}".format(n_currents))

    @classmethod
    def create_from_json(cls, json_dict: Dict) -> "IVCurve":
        """
        Create object from dict with structure compatible with UFIV JSON file schema.
        :param json_dict: dict with information about IV-curve.
        :return: IV-curve object.
        """

        return IVCurve(currents=json_dict["currents"], voltages=json_dict["voltages"])

    def to_json(self) -> Dict:
        """
        Return dict with structure compatible with UFIV JSON file schema.
        :return: dict with information about IV-curve.
        """

        return {
            "currents": self.currents,
            "voltages": self.voltages
        }


@dataclass
class Measurement(JsonConvertible):
    """
    Class for a single electrical IV-curve measurement.
    """

    settings: MeasurementSettings
    ivc: IVCurve
    comment: Optional[str] = None
    is_dynamic: Optional[bool] = None
    is_reference: Optional[bool] = None

    @classmethod
    def create_from_json(cls, json_data: Dict) -> "Measurement":
        """
        Create object from dict with structure compatible with UFIV JSON file schema.
        :param json_data: dict with information about measurement.
        :return: measurement object.
        """

        return Measurement(
            settings=MeasurementSettings.create_from_json(json_data["measurement_settings"]),
            ivc=IVCurve(currents=json_data["currents"], voltages=json_data["voltages"]),
            comment=json_data.get("comment"),
            is_dynamic=json_data.get("is_dynamic"),
            is_reference=json_data.get("is_reference")
        )

    def to_json(self) -> Dict:
        """
        Return dict with structure compatible with UFIV JSON file schema.
        :return: dict with information about measurement.
        """

        json_data = {
            "measurement_settings": self.settings.to_json(),
            "voltages": self.ivc.voltages,
            "currents": self.ivc.currents,
            "comment": self.comment,
            "is_dynamic": self.is_dynamic,
            "is_reference": self.is_reference,
        }
        return self.remove_unused(json_data)
