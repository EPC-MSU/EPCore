import unittest
from json import load
from os.path import join as join_path, dirname
from jsonschema import validate
from epcore.doc import path_to_ufiv_schema
from epcore.utils.converter_p10 import convert_p10

path_to_source = join_path(dirname(__file__), "p10.json")


class TestConverter(unittest.TestCase):

    def test_convert(self):
        with open(path_to_source, "r") as source:
            source_json = load(source)
        converted = convert_p10(source_json, "0.0.0")
        with open(path_to_ufiv_schema(), "r") as schema:
            schema_json = load(schema)
        validate(converted, schema_json)
