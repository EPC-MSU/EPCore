from dataclasses import dataclass
from typing import List, Dict, Optional
from .abstract import JsonConvertible


@dataclass
class MeasurementSettings(JsonConvertible):
    """
    Basic settings for IV Curve measurement.
    """

    sampling_rate: float
    internal_resistance: float
    max_voltage: float
    probe_signal_frequency: float
    precharge_delay: Optional[float] = None

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
class Point(JsonConvertible):
    current: float
    voltage: float

    def to_json(self) -> Dict:
        return {
            "current": self.current,
            "voltage": self.voltage
        }

    @classmethod
    def create_from_json(cls, json: Dict) -> "Point":
        return Point(current=json["current"], voltage=json["voltage"])


@dataclass
class Measurement(JsonConvertible):
    """
    Class for a single electrical IV-curve measurement.
    """

    settings: MeasurementSettings
    ivc: List[Point]
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
            "iv_array": [p.to_json() for p in self.ivc],
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
            ivc=[Point.create_from_json(p) for p in json_data["iv_array"]],
            comment=json_data.get("comment"),
            is_dynamic=json_data.get("is_dynamic"),
            is_reference=json_data.get("is_reference")
        )