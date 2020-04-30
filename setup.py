from setuptools import setup, find_packages


setup(
    version="1.0.0",
    name="epcore",
    packages=find_packages(),
    install_requires=[
        "dataclasses"  # for elements module
    ]
)
