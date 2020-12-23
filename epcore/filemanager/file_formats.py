from ..utils import convert_p10, convert_p10_2
import zipfile
from tempfile import TemporaryDirectory
from os.path import isfile, basename
import os
from PIL import Image
from ..elements import version
from json import load


class FileUFIVFormat:
    """
    Common class of board. Class not converters something and compatible with UFIV format file
    """
    json_pth = ""
    img_pth = ""

    def __init__(self, json_pth=None):

        if json_pth is None:
            return
        self.json_pth = json_pth
        self.find_img()

    def add_img_pth(self, img_pth):
        self.img_pth = img_pth

    def find_img(self):
        dir = os.path.dirname(self.json_pth)
        for f in os.listdir(dir):
            if ".png" in f or ".jpg" in f or ".bmp" in f:
                if f[:-4] == basename(self.json_pth)[:-5]:
                    self.add_img_pth(os.path.join(dir, f))

    def get_json_and_image(self):
        with open(self.json_pth, "r") as file:
            input_json = load(file)
        if self.img_pth is not None:
            image = Image.open(self.img_pth) if isfile(self.img_pth) else None
        return input_json, image


class FileP10NormalFormat(FileUFIVFormat):

    def __init__(self, path):
        super().__init__(json_pth=path)
        _dir = os.path.dirname(self.json_pth)
        if not isfile(self.img_pth):
            self.add_img_pth(os.path.join(_dir, "image.png"))

    def get_json_and_image(self, p10_convert_flag):
        """
        Function converters from p10 format to UFIV and return json file and image
        :param p10_convert_flag: True or False
        :return:
        """
        input_json, image = super().get_json_and_image()
        if p10_convert_flag:
            input_json = convert_p10(input_json, version=version, force_reference=True)
        return input_json, image


class FileP10NewFormat(FileUFIVFormat):

    def __init__(self, path):
        super().__init__(json_pth=path)
        _dir = os.path.dirname(self.json_pth)
        if not isfile(self.img_pth):
            self.add_img_pth(os.path.join(_dir, "image.png"))

    def get_json_and_image(self, p10_convert_flag):
        """
        Function converters from p10 format to UFIV and return json file and image
        :param p10_convert_flag:
        :return:
        """
        input_json, image = super().get_json_and_image()
        if p10_convert_flag:
            input_json = convert_p10_2(input_json, version=version, force_reference=True)
        return input_json, image


class FileArchivedUFIVFormat(FileUFIVFormat):

    def __init__(self, path):
        json_pth = self.convert_to_ufiv(path)
        super().__init__(json_pth=json_pth)

    def convert_to_ufiv(self, path):
        """
        Function convert UFIV_archived format to UFIV
        :param path:
        :return:
        """
        archive = zipfile.ZipFile(path, "r")
        tempdir = TemporaryDirectory().name
        archive.extractall(path=tempdir)
        archive.close()
        return os.path.join(tempdir, basename(path).replace(".uzf", ".json"))
