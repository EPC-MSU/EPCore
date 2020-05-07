from setuptools import setup


setup(
    version="1.0.1",
    name="epcore",
    packages=["epcore"],
    install_requires=[
        "dataclasses",  # for elements module
        "PyQt5>=5.8.2, <=5.14.0",  # for QImage and other ...
        "jsonschema"  # for converter (utils) and format validation (different tests)
    ]
)
