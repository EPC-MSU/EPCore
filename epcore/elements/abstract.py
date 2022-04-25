from abc import ABC, abstractmethod
from typing import Dict


class JsonConvertible(ABC):

    @classmethod
    @abstractmethod
    def create_from_json(cls, json: Dict) -> "JsonConvertible":
        """
        Create object from dict with info about object.
        :param json: dict with info.
        :return: object.
        """

        raise NotImplementedError()

    @classmethod
    def remove_unused(cls, source: Dict) -> Dict:
        """
        Remove all {"key": None} from source dictionary.
        :param source: source dictionary.
        :return: modified dictionary.
        """

        for key in list(source.keys()):
            if source[key] is None:
                source.pop(key)
        return source

    @abstractmethod
    def to_json(self) -> Dict:
        """
        Return dict with info about object.
        :return: dict with info.
        """

        raise NotImplementedError()
