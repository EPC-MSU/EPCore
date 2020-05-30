from PIL import Image


def save_screenshot(image: Image.Image, path: str):
    """
    Save screenshot to path
    :param image: PIL Image
    :param path: path to target file
    :return:
    """
    image.save(path)  # ... that's all
