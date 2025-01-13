""" Installation instructions for the Cubigma cryptography library. """

from os import path

from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="cubigma",
    version="0.1.0",
    description="This library implements a 3-dimensional playfair cipher with augmented encryption logic.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://pypi.org/project/cubigma",
    author="Mark Rogers",
    author_email="cubigma@titanminds.com",
    license="AGPL-3.0-or-later",
    license_files=["LICENSE"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Information Technology",
        "Topic :: Security :: Cryptography",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="development",
    packages=find_packages(exclude=["contrib", "docs", "resources", "tests*"]),
    install_requires=["pillow^=11.0", "regex^=2024.11"],
)
