from setuptools import find_packages, setup

NAME = "superpathlib"


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
    download_url="https://github.com/quintenroets/superpathlib/archive/refs/tags/v0.0.1.tar.gz",
    description="extended pathlib",
    name=NAME,
    version="0.0.1",
    packages=find_packages(),
    install_requires=read("requirements.txt"),
)
