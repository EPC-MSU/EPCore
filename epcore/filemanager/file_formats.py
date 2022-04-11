import json
import os
import zipfile
from tempfile import TemporaryDirectory
from typing import Optional, Tuple
from PIL import Image, ImageOps
from ..elements import version
from ..utils import convert_p10, convert_p10_2


class FileUFIVFormat:
    """
    Common class for board files (in UFIV format).
    """

    def __init__(self, json_path: str = None):
        """
        :param json_path: path to json file.
        """

        self.img_pth: str = ""
        self.json_pth: str = ""
        if json_path is None:
            return
        self.json_pth = json_path
        self.find_img()

    def add_img_pth(self, img_path: str):
        """
        :param img_path: path to image of board.
        """

        self.img_pth = img_path

    def find_img(self):
        """
        Method finds board image in directory containing json file.
        """

        directory = os.path.dirname(self.json_pth)
        for f in os.listdir(directory):
            if os.path.splitext(f)[-1] in (".png", ".jpg", ".bmp"):
                if f[:-4] == os.path.basename(self.json_pth)[:-5]:
                    self.add_img_pth(os.path.join(directory, f))

    def get_json_and_image(self) -> Tuple:
        """
        Method returns json file and image of board.
        :return: json file content and image of board.
        """

        with open(self.json_pth, "r") as file:
            input_json = json.load(file)
        image = None
        if self.img_pth and os.path.isfile(self.img_pth):
            image = Image.open(self.img_pth)
            image = ImageOps.exif_transpose(image)
        return input_json, image


class FileP10NormalFormat(FileUFIVFormat):
    """
    Class for board files in P10 normal format.
    """

    def __init__(self, path: str):
        """
        :param path: path to json file.
        """

        super().__init__(path)
        self.convert_func = convert_p10

    def find_img(self):
        """
        Method finds board image in directory containing json file.
        """

        dir_name = os.path.dirname(self.json_pth)
        img_path = os.path.join(dir_name, "image.png")
        if os.path.isfile(img_path):
            self.add_img_pth(img_path)

    def get_json_and_image(self, p10_convert_flag: bool) -> Tuple:
        """
        Method converts from P10 format to UFIV and returns json file and image of board.
        :param p10_convert_flag: if True json file content will be converted to UFIV format.
        :return: json file content and image of board.
        """

        input_json, image = super().get_json_and_image()
        if p10_convert_flag:
            input_json = self.convert_func(input_json, version=version, force_reference=True)
        return input_json, image


class FileP10NewFormat(FileP10NormalFormat):
    """
    Class for board files in P10 new format.
    """

    def __init__(self, path: str):
        """
        :param path: path to json file.
        """

        super().__init__(path)
        self.convert_func = convert_p10_2


class FileArchivedUFIVFormat(FileUFIVFormat):
    """
    Class for board files in UFIV zipped format.
    """

    def __init__(self, path: str):
        """
        :param path: path to UFIV zipped file.
        """

        json_path = self.convert_to_ufiv(path)
        super().__init__(json_path)

    @staticmethod
    def convert_to_ufiv(path: str) -> Optional[str]:
        """
        Method extracts content from UFIV zipped file and returns path to extracted json file.
        :param path: path to UFIV zipped file.
        :return: path to extracted json file.
        """

        with zipfile.ZipFile(path, "r") as archive:
            temp_dir = TemporaryDirectory().name
            archive.extractall(path=temp_dir)
            for filename in archive.namelist():
                if os.path.splitext(filename)[-1] == ".json":
                    return os.path.join(temp_dir, filename)
        return None
