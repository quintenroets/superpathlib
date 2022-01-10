# superpathlib
Extended pathlib with extra functionality

## Installation

```shell
pip install git+https://github.com/quintenroets/superpathlib
```

## Usage
Use 

```shell
from plib import Path
```
instead of

```shell
from pathlib import Path
```

To gain access to additional functionality on path instances such as:
* Load and save generic structures to files:
    * save(): write generic structure to path
    * load(): load generic structure from path
    * C implementations used (much faster)
* Error handling:
    * Automatically create parents when parent of written file does not exist
    * Automatically return default value when accessing nonexistent files
* Additional functions:
    * write(): write content to file with dynamic check of content type to determine correct format
    * find(): recursively find all paths under a path that match a condition with extra options for efficiency
    * rmtree(): remove directory recursively
    * ..
* Additional properties to read/write to file in particular format:
    * content
    * text
    * byte_content
    * lines
    * json
    
    * example usage: 

        ```shell
        path1.lines = [line for line in path2.lines if skip_content not in line]
        path.json = {key: value}
        ```
* Access to additional properties:
    * is_root: whether path or first existing parent is owned by root user
    * mtime: modified time of the path
    * size: size of the content in the path
    * tag: tag assigned to path: can be used for alternative ordering or metadata
* Easily set path properties (Linux only):
    * mtime: path.mtime = timestamp -> sets the modified time of a path instance to timestamp
    * tag: path.tag = value -> sets the tag value of a path instance

Or inherit from this class to define your own additional functionality:

```shell
from plib import Path as BasePath

class Path(BasePath):
    def count_children(self):
        return len(list(self.iterdir()))
```

This will not work if you inherit from pathlib.Path instead
