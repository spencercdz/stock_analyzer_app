from setuptools import setup, Extension
import pybind11

ext_modules = [
    Extension(
        'dcf_calculator',                          # The name of the C++ extension
        ['main/dcf_calculator.cpp'],                 # Path to your C++ file
        include_dirs=[pybind11.get_include()]  # Include pybind11 headers
    )
]

setup(
    name='predictor',
    ext_modules=ext_modules,
)
