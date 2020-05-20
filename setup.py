from setuptools import setup, find_packages


setup(
    version="1.0.1",
    name="epcore",
    packages=find_packages(),
    install_requires=[
        "dataclasses",  # for elements module
        "Pillow",  # for Board image class
        "jsonschema",  # for converter (utils) and format validation (different tests)
        "numpy"  # for test_iv_curve
    ],
    package_data={
        "epcore.ivmeasurer": ["ivmeasurer/ivm-debian/libivm.so",
                              "ivmeasurer/ivm-win32/ivm.dll",
                              "ivmeasurer/ivm-win64/ivm.dll"],
        "epcore.measurementmanager": ["measurementmanager/ivcmp-debian/libivcmp.so",
                                      "measurementmanager/ivcmp-win32/ivcmp.dll",
                                      "measurementmanager/ivcmp-win64/ivcmp.dll"]
    }
)
