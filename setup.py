from pathlib import Path

from setuptools import find_packages, setup

NAME = "superpathlib"
version = "0.0.6"


def read(filename):
    try:
        with open(filename) as fp:
            content = fp.read().split("\n")
    except FileNotFoundError:
        content = []
    return content


setup(
    author="Quinten Roets",
    author_email="quinten.roets@gmail.com",
    url="https://github.com/quintenroets/superpathlib",
    download_url=(
        "https://github.com/quintenroets/"
        f"superpathlib/archive/refs/tags/v{version}.tar.gz"
    ),
    description="extended pathlib",
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    name=NAME,
    version=version,
    packages=find_packages(),
    install_requires=read("requirements.txt"),
    python_requires=">3.9",
)
