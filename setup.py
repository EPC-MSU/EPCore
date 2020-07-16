from setuptools import setup, find_packages


setup(
    version="0.1.2",
    name="epcore",
    packages=find_packages(),
    install_requires=[
        "dataclasses",  # for elements module
        "Pillow",  # for Board image class
        "jsonschema",  # for converter (utils) and format validation (different tests)
        "numpy",  # for test_iv_curve
        "scipy"  # for curve interpolation
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
