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
* Generic structures:
    * save(): write generic structure to path
    * load(): load generic structure from path
    * C implementations used (much faster)
* Error handling:
    * Automatically create parents when parent of written file does not exist
    * Automatically return default value when accessing nonexistent files
* Additional functions:
    * is_root(): whether path or first existing parent is owned by root user
    * write: write content to file with dynamic check of content type to determine correct format
    * find: recursively find all paths under a path that match a condition with extra options for efficiency
    * ..

Or inherit from this class to define your own additional functionality:

```shell
from plib import Path as BasePath

class Path(BasePath):
    def count_childer(self):
        return len(list(self.iterdir()))
```

This will not work if you inherit from pathlib.Path instead
