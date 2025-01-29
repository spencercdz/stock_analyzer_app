from setuptools import setup, Extension
import pybind11

dcf_calculator = [
    Extension(
        name='dcf_calculator',                          # The name of the C++ extension
        sources=['main/dcf_calculator.cpp'],                 # Path to your C++ file
        include_dirs=[pybind11.get_include()],  # Include pybind11 headers
        language='c++',
    )
]

setup(
    name='dcf_calculator',
    version='0.1',
    ext_modules=[dcf_calculator],  # Add the extension module
    zip_safe=False,
)