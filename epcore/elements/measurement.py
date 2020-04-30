from typing import List, Dict
import logging


class MeasurementSettings:
    """
    Basic settings for IV Curve measurement.
    """
    def __init__(self):
        pass

    def to_json_dict(self) -> Dict:
        """
        Return object as dict with structure
        compatible with UFIV JSON file schema
        """
        return {}

    @classmethod
    def create_from_json_dict(cls, json_data: Dict) -> "MeasurementSettings":
        """
        Create object from dict with structure
        compatible with UFIV JSON file schema
        """
        return MeasurementSettings()


class IVCurve:
    """
    IVCurve data.
    Measurement results only.
    """
    def __init__(self, currents: Optional[List[float]] = None, voltages: Optional[List[float]] = None):
        self.currents = currents or []
        self.voltages = voltages or []

    def to_json_dict(self) -> Dict:
        """
        Return object as dict with structure
        compatible with UFIV JSON file schema
        """
        json_data = dict()
        json_data["voltage"] = self.voltages
        json_data["current"] = self.currents
        return json_data

    @classmethod
    def create_from_json_dict(cls, json_data: Dict) -> "IVCurve":
        """
        Create object from dict with structure
        compatible with UFIV JSON file schema
        """
        return IVCurve(
            currents=json_data["current"],
            voltages=json_data["voltage"]
        )


class Measurement:
    """
    Class for a single electrical IV-curve measurement.
    """
    def __init__(self,
                 is_reference: bool = False,
                 settings: MeasurementSettings = MeasurementSettings(),
                 iv_curve: IVCurve = IVCurve()):
        logging.debug("New measurement created")
        self.is_reference = is_reference
        self.settings = settings
        self.iv_curve = iv_curve

    def to_json_dict(self) -> Dict:
        """
        Return object as dict with structure
        compatible with UFIV JSON file schema
        """
        json_data = dict()
        json_data["is_reference"] = self.is_reference
        json_data["measurement_settings"] = self.settings.to_json_dict()
        json_data["iv_array"] = []
        json_data["iv_array"].append(self.iv_curve.to_json_dict())
        return json_data

    @classmethod
    def create_from_json_dict(cls, json_data: Dict) -> "Measurement":
        """
        Create object from dict with structure
        compatible with UFIV JSON file schema
        """
        return Measurement(
            is_reference=json_data["is_reference"],
            settings=MeasurementSettings.create_from_json_dict(
                json_data["measurement_settings"]),
            iv_curve=IVCurve.create_from_json_dict(json_data["iv_array"][0])
        )
