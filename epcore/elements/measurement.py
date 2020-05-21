from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .abstract import JsonConvertible


@dataclass
class MeasurementSettings(JsonConvertible):
    """
    Basic settings for IV Curve measurement.
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

    def to_json(self) -> Dict:
        """
        Return object as dict with structure
        compatible with UFIV JSON file schema
        """

        json_data = {
            "sampling_rate": self.sampling_rate,
            "internal_resistance": self.internal_resistance,
            "max_voltage": self.max_voltage,
            "probe_signal_frequency": self.probe_signal_frequency,
            "precharge_delay": self.precharge_delay
        }

        return self.remove_unused(json_data)

    @classmethod
    def create_from_json(cls, json_data: Dict) -> "MeasurementSettings":
        """
        Create object from dict with structure
        compatible with UFIV JSON file schema
        """
        return MeasurementSettings(
            sampling_rate=json_data["sampling_rate"],
            internal_resistance=json_data["internal_resistance"],
            max_voltage=json_data["max_voltage"],
            probe_signal_frequency=json_data["probe_signal_frequency"],
            precharge_delay=json_data.get("precharge_delay")
        )


@dataclass
class IVCurve(JsonConvertible):
    """
    IVCurve data.
    Measurement results only.
    """
    currents: List[float] = field(default_factory=lambda: [0., 0.])
    voltages: List[float] = field(default_factory=lambda: [0., 0.])

    def __post_init__(self):
        if len(self.currents) != len(self.voltages):
            raise ValueError("""Currents and voltages array lengths should be equal.
                                Got len(currents) = {}. len(voltages) = {}""".format(
                                    len(self.currents), len(self.voltages)
                                ))

        if len(self.currents) < 2:
            raise ValueError("""IV curve should contain at lease 2 points
                                for correct operation, got {}""".format(
                                    len(self.currents)
                                ))

    def to_json(self) -> Dict:
        return {
            "currents": self.currents,
            "voltages": self.voltages
        }

    @classmethod
    def create_from_json(cls, json: Dict) -> "IVCurve":
        return IVCurve(currents=json["currents"], voltages=json["voltages"])


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

    def to_json(self) -> Dict:
        """
        Return object as dict with structure
        compatible with UFIV JSON file schema
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

    @classmethod
    def create_from_json(cls, json_data: Dict) -> "Measurement":
        """
        Create object from dict with structure
        compatible with UFIV JSON file schema
        """
        return Measurement(
            settings=MeasurementSettings.create_from_json(json_data["measurement_settings"]),
            ivc=IVCurve(currents=json_data["currents"], voltages=json_data["voltages"]),
            comment=json_data.get("comment"),
            is_dynamic=json_data.get("is_dynamic"),
            is_reference=json_data.get("is_reference")
        )
