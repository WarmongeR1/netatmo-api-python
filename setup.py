#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python setup.py --dry-run --verbose install

from setuptools import setup, find_packages

setup(
    name='lnetatmo',
    version='0.7.0',
    author='Philippe Larduinat, Alexander Sapronov',
    author_email='sapronov.alexander92@gmail.com',
    packages=find_packages(),
    url='https://github.com/WarmongeR1/netatmo-api-python',
    license='Open Source',
    description='Simple API to access Netatmo weather station data from any python script.',
    long_description=open('README.md').read(),
    include_package_data=True,
)
