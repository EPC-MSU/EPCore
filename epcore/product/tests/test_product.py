import unittest
from epcore.product import EPLab, InvalidJson
from epcore.ivmeasurer import IVMeasurerVirtual


class TestEPLabProduct(unittest.TestCase):
    def test_rw_settings(self):
        measurer = IVMeasurerVirtual()

        eplab = EPLab()

        options = {
            EPLab.Parameter.frequency: "100hz",
            EPLab.Parameter.sensitive: "middle",
            EPLab.Parameter.voltage: "3.3v"
        }
        settings = measurer.get_settings()
        settings = eplab.options_to_settings(options, settings)
        measurer.set_settings(settings)
        settings = measurer.get_settings()

        self.assertTrue(options == eplab.settings_to_options(settings))

    def test_invalid_json(self):
        with self.assertRaises(InvalidJson):
            EPLab(dict())

        with self.assertRaises(InvalidJson):
            EPLab({
                "options": {
                    "frequency": [],
                    "voltage": [],
                    "sensitive": [],
                    "eggs": []
                },
                "plot_parameters": {
                    "test_color": "#0000FF",
                }
            })

    def test_some_json(self):
        data = {
                "options": {
                    "frequency": [
                        {
                            "name": "FREQ1",
                            "value": [1, 1],
                            "label_ru": "частота1",
                            "label_en": "freq1"
                        },
                        {
                            "name": "FREQ2",
                            "value": [2, 2],
                            "label_ru": "частота1",
                            "label_en": "freq1"
                        }
                    ],
                    "sensitive": [
                        {
                            "name": "SENS1",
                            "value": 4,
                            "label_ru": "ч1",
                            "label_en": "s1"
                        }
                    ],
                    "voltage": [
                        {
                            "name": "VOLT1",
                            "value": 9,
                            "label_ru": "в1",
                            "label_en": "v1"
                        }
                    ]
                },
                "plot_parameters": {
                    "test_color": "#0000FF",
                    "ref_color": "#FF0000"
                }
            }
        eplab = EPLab(data)
        options = eplab.get_all_available_options()

        self.assertTrue(len(options[EPLab.Parameter.voltage].options) == len(data["options"]["voltage"]))
        self.assertTrue(options[EPLab.Parameter.voltage].options[0].value == data["options"]["voltage"][0]["value"])
        self.assertTrue(len(options[EPLab.Parameter.frequency].options) == len(data["options"]["frequency"]))
        self.assertTrue(options[EPLab.Parameter.frequency].options[1].name == data["options"]["frequency"][1]["name"])
        self.assertTrue(options[EPLab.Parameter.frequency].options[1].label_ru ==
                        data["options"]["frequency"][1]["label_ru"])
        self.assertTrue(options[EPLab.Parameter.frequency].options[1].label_en ==
                        data["options"]["frequency"][1]["label_en"])
        self.assertTrue(options[EPLab.Parameter.frequency].options[1].value == data["options"]["frequency"][1]["value"])
        self.assertTrue(eplab.plot_parameters.ref_color == data["plot_parameters"]["ref_color"])
        self.assertTrue(eplab.plot_parameters.test_color == data["plot_parameters"]["test_color"])
