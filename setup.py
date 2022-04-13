from setuptools import setup, find_packages


setup(
    version="0.1.6",
    name="epcore",
    packages=find_packages(),
    install_requires=[
        "dataclasses==0.8",  # for elements module
        "Pillow==8.0.1",  # for Board image class
        "jsonschema==3.2.0",  # for converter (utils) and format validation (different tests)
        "numpy==1.18.1",  # for test_iv_curve
        "scipy==1.5.4"  # for curve interpolation
    ],
    package_data={
        "epcore.analogmultiplexer": ["epmux/epmux-debian/libepmux.so",
                                     "epmux/epmux-win32/epmux.dll",
                                     "epmux/epmux-win64/epmux.dll"],
        "epcore.ivmeasurer": ["ivm02/ivm-debian/libivm.so",
                              "ivm02/ivm-win32/ivm.dll",
                              "ivm02/ivm-win64/ivm.dll",
                              "ivm10/ivm-arm64/libivm.so",
                              "ivm10/ivm-debian/libivm.so",
                              "ivm10/ivm-win32/ivm.dll",
                              "ivm10/ivm-win64/ivm.dll",
                              "asa10/libasa-debian/libasa.so",
                              "asa10/libasa-debian/libxmlrpc.so.3.51",
                              "asa10/libasa-debian/libxmlrpc_client.so.3.51",
                              "asa10/libasa-debian/libxmlrpc_util.so.4.51",
                              "asa10/libasa-debian/libxmlrpc_xmlparse.so.3.51",
                              "asa10/libasa-debian/libxmlrpc_xmltok.so.3.51",
                              "asa10/libasa-win32/asa.dll",
                              "asa10/libasa-win32/libxmlrpc.dll",
                              "asa10/libasa-win32/libxmlrpc_client.dll",
                              "asa10/libasa-win32/libxmlrpc_util.dll",
                              "asa10/libasa-win32/libxmlrpc_xmlparse.dll",
                              "asa10/libasa-win32/libxmlrpc_xmltok.dll",
                              "EyePoint_settings.json",
                              "EyePoint_virtual_device_settings.json",
                              "ASA_device_settings.json",
                              "asa10/eplab_asa_options.json"],
        "epcore.measurementmanager": ["ivcmp-arm64/libivcmp.so",
                                      "ivcmp-debian/libivcmp.so",
                                      "ivcmp-win32/ivcmp.dll",
                                      "ivcmp-win64/ivcmp.dll"],
        "epcore.doc": ["p10_elements.schema.json",
                       "p10_elements_2.schema.json",
                       "ufiv.schema.json"],
        "epcore.product": ["doc/eplab_schema.json",
                           "eplab_default_options.json"]
    }
)
