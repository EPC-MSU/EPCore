"""
Default path manager
https://ximc.ru/issues/39201
"""
import os.path as path
from os import makedirs, listdir
import re
from typing import Optional


class DefaultPathError(OSError):
    pass


class DefaultPathManager:
    def __init__(self, device: str, subdir: str = "", prefix: str = "board", postfix: str = "json"):
        """
        Create default path manager
        :param device: path to default root directory (path to usb flash drive, e.g. /mount/drive)
        :param subdir: path to sub-directory (e.g. eyepoint/screenshots)
        :param prefix: files prefix (e.g. "board" or "screen")
        :param postfix: files postfix (e.g. "json" or "png")
        """
        self._device = device
        self._subdirs = subdir
        self._directory = path.join(device, subdir)

        self._template_r = re.compile(prefix + r"_(?P<number>\d+)\." + postfix)
        self._template_f = prefix + "_{0}." + postfix

    def _prepare_directory(self):
        if not self.is_default_path_available():
            raise DefaultPathError("Directory " + self._device + " does not exists")

        if not path.isdir(self._directory):
            try:
                makedirs(self._directory, exist_ok=True)
            except OSError as err:
                raise DefaultPathError(err)

    def _last_file(self) -> Optional[str]:
        """
        Get last board file in directory
        :return: file name (str)
        """
        self._prepare_directory()

        matches = [re.match(self._template_r, file) for file in listdir(self._directory)]
        matches = sorted(filter(None, matches), key=lambda match: int(match["number"]))

        return matches[-1].string if matches else None

    def save_file_path(self) -> str:
        """
        Get path to save the next UFIV file
        :return: full path (str)
        """
        file = self._last_file()
        index = int(self._template_r.match(file)["number"]) + 1 if file else 0

        return path.join(self._directory, self._template_f.format(str(index)))

    def open_file_path(self) -> Optional[str]:
        """
        Get path to last UFIV file
        :return: full path (str)
        """
        file = self._last_file()
        return path.join(self._directory, file) if file else None

    def is_default_path_available(self) -> bool:
        """
        Check if the default path is available
        :return: bool (available / not available)
        """
        return path.isdir(self._device)
