from setuptools import setup, Extension, find_packages
import pybind11

dcf_calculator = Extension(
    name='dcf_calculator',
    sources=['main/dcf_calculator.cpp'],
    include_dirs=[pybind11.get_include()],
    language='c++',
    extra_compile_args=['-std=c++11'],  # Ensure C++11 compatibility
)

setup(
    name='dcf_calculator',
    version='0.1',
    ext_modules=[dcf_calculator],
    packages=find_packages(),
    install_requires=[
        'Flask>=2.3.2',
        'Flask-Cors>=3.0.10',
        'gunicorn>=20.1.0',
        'yfinance>=0.2.55',
        'pandas>=2.1.1',
        'numpy>=1.24.3',
        'matplotlib>=3.7.2',
        'requests>=2.31.0',
        'beautifulsoup4>=4.13.3',
        'pybind11>=2.10.4',
        'python-dotenv>=1.0.0',
    ],
    zip_safe=False,
)