#!/usr/bin/env python

try:
    from setuptools import setup
except:
    from distutils.core import setup

setup(
    name="forgeosi",
    version=1.0,
    packages=["forgeosi",
              "forgeosi.lib"],
    author="Maximilian Krueger",
    author_email="maximilian.krueger@fau.de",
    url="https://github.com/maxfragg/forgeosi",
    description="A forensic generator for operating system images",
    long_description=open('README.md').read(),
    license="simplified BSD",
    zip_safe=False,
    install_requires=['pyvbox', 'enum34', 'decorator'],
    platforms=['cygwin', 'linux'],
)
