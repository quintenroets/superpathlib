# Superpathlib
[![PyPI version](https://badge.fury.io/py/superpathlib.svg)](https://badge.fury.io/py/superpathlib)
![PyPI downloads](https://img.shields.io/pypi/dm/superpathlib)
![Python version](https://img.shields.io/badge/python-3.10+-brightgreen)
![Operating system](https://img.shields.io/badge/os-linux%20%7c%20macOS-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)

Maximize your productivity with minimal code!

Superpathlib is an enhanced version of Python's standard [pathlib](https://docs.python.org/3/library/pathlib.html), designed to make file operations more intuitive and extend functionality without compromising performance. It builds on pathlib by introducing additional properties, methods, and shortcuts that simplify common file manipulations and reduce boilerplate code.

For custom operations, the package supports subclassing, which has been added to the standard library in [python3.12](https://docs.python.org/3/whatsnew/3.12.html).

## Key features:
* Read and write content in various formats such as text, bytes, YAML, JSON, and even NumPy arrays
* Access and modify file metadata like file size, modification time, and custom tags
* Utility methods:
    * `rmtree` to remove directories recursively
    * `copy_to` to copy content
    * `tempfile` to create and use temporary files
    * `find` for recursive search
    * `unpack` for unpacking archives

## Usage

```shell
from superpathlib import Path

path = Path(filename)
```

### 1) Use properties to read & write path content in different formats
* text
* byte_content
* lines
* yaml
* json
* numpy

examples:

```shell
path.json = {key: value}

for line in path.lines:
    if interesting(line):
        process(line)
```
### 2) Use instance properties to get/set file metadata:
* get:
    * size: filesize
    * is_root: whether the owner of the file is a root user
    * has_children: whether a path has children
    * number_of_children: number of children in a folder
    * filetype: content type of a file
    * content_hash: a hash of the complete substructure found in a folder
* get & set:
    * mtime: modified time
    * tag: can be used for alternative ordering or metadata

examples:

```shell
path_new.mtime = path_old.mtime

if path.tag != skip_keyword and path.filetype == "video":
    process(path)
```
### 3) Use class properties to access commonly used folders:
* docs
* assets
* ..

example:

```shell
names_path = Path.assets / 'names'
names = names_path.lines
```
### 4) Use additional functionality
* find(): recursively find all paths under a root that match a condition (extra options available for performance optimization)
* rmtree(): remove directory recursively
* copy_to(dest): copy content to dest
* copy_properties_to(dest): recursively copy path properties (mtime, tag) to all n-level children of dest
* tempfile(): create temporary file that can be used as context manager
* unpack(): extract archive(zip, tar, ..) file to desired folder
* pop_parent(): remove first parent from path in filesystem
* from_uri(uri): create path object from uri string

examples:

```shell
with Path.tempfile() as tmp:
    do_work(logfile=tmp)
    log = tmp.text
process(log)

is_git_root = lambda p: (p / '.git').exists()
for git_path in root.find(is_git_root):
    process_git(git_path)
```
### 5) Enhance existing functionality
* Automatically create parents when writing files, creating new files, renaming files, ..
* Return default values when path does not exist (e.g. size = 0, lines=[])
* Support replacing folders instead files only if specified

### 6) Inherit from superpathlib Path to define your own additional functionality:

example:

```shell
import superpathlib

class Path(superpathlib.Path):
    def count_children(self):
        return sum(1 for _ in self.iterdir())
```

The standard pathlib library supports this for Python versions starting from [python3.12](https://docs.python.org/3/whatsnew/3.12.html).

## Installation

```shell
pip install superpathlib
```
or
```shell
pip install superpathlib[full]
```
to include additional dependencies like PyYAML for handling YAML files

or

Manually install the packages corresponding with the features you want to use:
* Packages listed in pyproject.toml
