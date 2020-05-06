from setuptools import setup, find_packages


setup(
    version="1.0.0",
    name="epcore",
    packages=find_packages(),
    install_requires=[
        "dataclasses",  # for elements module
        "PyQt5>=5.8.2, <=5.14.0",  # for QImage and other ...
    ]
)
