#!/usr/bin/env python

try:
    from setuptools import setup
except:
    from distutils.core import setup

import re
import platform
import os
import sys


setup(
    name="forgeosi",
    version=0.8,
    packages=["forgeosi",
              "forgeosi.lib"],
    author="Maximilian Krueger",
    author_email="maximilian.krueger@fau.de",
    url="https://github.com/maxfragg/forgeosi",
    description="A forensic generator for operating system images",
    long_description=open('README.md').read(),
    license="GNU GPL v3",
    zip_safe=False,
    install_requires = ['pyvbox', 'enum34', 'decorator'],
    platforms=['cygwin', 'linux'],
)
