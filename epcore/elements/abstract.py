from typing import Dict
from abc import ABC, abstractmethod


class JsonConvertible(ABC):
    @classmethod
    @abstractmethod
    def create_from_json(cls, json: Dict) -> "JsonConvertible":
        raise NotImplementedError()

    @abstractmethod
    def to_json(self) -> Dict:
        raise NotImplementedError()

    @classmethod
    def remove_unused(cls, source: Dict) -> Dict:
        """
        Remove all {"key": None} from dictionary
        :param source:
        """
        for key in list(source.keys()):
            if source[key] is None:
                source.pop(key)
        return source
