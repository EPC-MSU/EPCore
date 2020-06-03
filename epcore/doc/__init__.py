from os.path import dirname, join as join_path

_path_to_ufiv_schema = join_path(dirname(__file__), "ufiv.schema.json")


def path_to_ufiv_schema() -> str:
    return _path_to_ufiv_schema


__all__ = ["path_to_ufiv_schema"]
