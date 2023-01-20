# Superpathlib
Superpathlib offers Path objects with functionality extended from pathlib to maximize your productivity with a minimal amount of code.

## Usage

```shell
from plib import Path
path = Path(filename)
```

### 1) Use properties to read & write path content in different formats
* text
* byte_content
* lines
* yaml
* json

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

examples: 

```shell
with Path.tempfile() as tmp:
    do_work(logfile=tmp)
    log = tmp.text
process(log)

condition = lambda p: (p / '.git').exists()
for git_path in root.find(condition):
    process_git(git_path)
```
### 5) Enhance existing functionality
* Automatically create parents when writing files, creating new files, renaming files, ..
* Return default values when path does not exist (e.g. size = 0, lines=[])

### 6) Inherit from Path to define your own additional functionality:

example: 

```shell
from plib import Path as BasePath

class Path(BasePath):
    def count_children(self):
        return sum(1 for _ in self.iterdir())
```

This only works if you inherit from plib and not from the builtin pathlib


## Installation

```shell
pip install superpathlib
requires python version >= 3.9
```
