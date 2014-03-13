#!/usr/bin/env python
from setuptools import setup

import re
import platform
import os
import sys


install_requires = []

tests_require = ['virtualbox', 'enum34', 'decorator']

setup(
    name="forgeosi",
    version=0.8,
    packages=["forgeosi",
              "forgeosi.lib"],
    author="Maximilian Krüger",
    author_email="maximilian.krueger@fau.de",
    url="https://github.com/maxfragg/forgeosi",
    description="A forensic generator for operating system images",
    long_description=open('README.md').read(),
    license="GNU GPL v3",
    zip_safe=False,
    install_requires = install_requires,
    platforms=['cygwin', 'linux'],
)
