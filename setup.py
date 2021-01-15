from setuptools import setup, find_packages


setup(
    version="0.1.6",
    name="epcore",
    packages=find_packages(),
    install_requires=[
        "dataclasses==0.8",  # for elements module
        "Pillow==8.0.1",  # for Board image class
        "jsonschema==3.2.0",  # for converter (utils) and format validation (different tests)
        "numpy==1.14.5",  # for test_iv_curve
        "scipy==1.5.4"  # for curve interpolation
    ],
    package_data={
        "epcore.ivmeasurer": ["ivm-debian/libivm.so",
                              "ivm-win32/ivm.dll",
                              "ivm-win64/ivm.dll"],
        "epcore.measurementmanager": ["ivcmp-debian/libivcmp.so",
                                      "ivcmp-win32/ivcmp.dll",
                                      "ivcmp-win64/ivcmp.dll"],
        "epcore.doc": ["p10_elements.schema.json",
                       "p10_elements_2.schema.json",
                       "ufiv.schema.json"],
    }
)
