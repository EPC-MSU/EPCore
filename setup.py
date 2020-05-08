from setuptools import setup, find_packages


setup(
    version="1.0.1",
    name="epcore",
    packages=find_packages(),
    install_requires=[
        "dataclasses",  # for elements module
        "PyQt5>=5.8.2, <=5.14.0",  # for QImage and other ...
        "jsonschema",  # for converter (utils) and format validation (different tests)
        "numpy"  # for test_iv_curve
    ],
    package_data={
        "epcore.ivmeasurer": ["ivmeasurer/ivm.dll",
                              "ivmeasurer/ivm.lib",
                              "ivmeasurer/libivm.so"]  # for ivmeasurer module (ivm library)
    }
)
