#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

from catt import __version__

if sys.version_info.major < 3:
    print("This program requires Python 3 and above to run.")
    sys.exit(1)


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open("README.rst") as readme_file:
    readme = readme_file.read()

requirements = [
    "youtube-dl>=2020.9.20",
    "PyChromecast>=9.0.0",
    "Click>=7.1.2,<8",
    "ifaddr>=0.1.7",
    "requests>=2.23.0",
    'typing;python_version<"3.5"',
]

test_requirements = []  # type: ignore

setup(
    name="catt",
    version=__version__,
    description="Cast All The Things allows you to send videos from many, many online sources to your Chromecast.",
    long_description=readme,
    author="Stavros Korokithakis",
    author_email="hi@stavros.io",
    url="https://github.com/skorokithakis/catt",
    packages=["catt"],
    package_dir={"catt": "catt"},
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords="chromecast cast catt cast_all_the_things",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    test_suite="tests",
    tests_require=test_requirements,
    python_requires=">=3.4",
    entry_points={"console_scripts": ["catt=catt.cli:main"]},
)
