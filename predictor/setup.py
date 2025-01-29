from setuptools import setup, Extension
import pybind11

dcf_calculator = Extension(
    name='dcf_calculator',                  
    sources=['main/dcf_calculator.cpp'],   
    include_dirs=[pybind11.get_include()],       
    language='c++',
)

setup(
    name='dcf_calculator',
    version='0.1',
    ext_modules=[dcf_calculator],
    zip_safe=False,
)