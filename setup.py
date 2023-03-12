#!/usr/bin/env python
from os.path import abspath, dirname, join
from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().strip().splitlines()


source_directory = dirname(abspath(__file__))

setup(
    name='inspectorper',
    version='0.0.1',
    python_requires='>=3.6',
    description='standalone web server for investigating performance',
    author='Alexander Lyabah',
    author_email='a.lyabah@checkio.org',
    url='https://github.com/oduvan/inspectper',
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': ['inspectper = inspectper.server:main'],
    },
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)
