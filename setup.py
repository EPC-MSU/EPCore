from setuptools import setup, find_packages


setup(
    version="3.0.0",
    name='epcore',
    packages=find_packages(),
    install_requires=[
        "numpy"  # for pin module
    ],
    #package_dir = {'': 'epcore'},
    package_data={
        'epcore.sound': ['sound/foo.so']  # for sound module
    }
)
