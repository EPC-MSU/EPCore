from os.path import dirname, join as join_path

_path_to_schema = join_path(dirname(__file__), "elements.schema.json")


def path_to_schema() -> str:
    return _path_to_schema


__all__ = ["path_to_schema"]
