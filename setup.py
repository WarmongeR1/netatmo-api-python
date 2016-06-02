# -*- coding: utf-8 -*-

# python setup.py --dry-run --verbose install

from distutils.core import setup

setup(
    name='lnetatmo',
    version='0.5.0',
    author='Philippe Larduinat',
    author_email='philippelt@users.sourceforge.net',
    py_modules=['lnetatmo'],
    scripts=[],
    data_files=[],
    url='https://github.com/WarmongeR1/netatmo-api-python',
    license='Open Source',
    description='Simple API to access Netatmo weather station data from any python script.',
    long_description=open('README.md').read()
)
