from os.path import dirname, join as join_path

_path_to_ufiv_schema = join_path(dirname(__file__), "ufiv.schema.json")
_path_to_p10_elements_schema = join_path(dirname(__file__), "p10_elements.schema.json")
_path_to_p10_elements_2_schema = join_path(dirname(__file__), "p10_elements_2.schema.json")


def path_to_ufiv_schema() -> str:
    return _path_to_ufiv_schema


def path_to_p10_elements_schema() -> str:
    return _path_to_p10_elements_schema


def path_to_p10_elements_2_schema() -> str:
    return _path_to_p10_elements_2_schema


__all__ = ["path_to_ufiv_schema",
           "path_to_p10_elements_schema",
           "path_to_p10_elements_2_schema"]
