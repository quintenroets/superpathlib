# superpathlib
Extended pathlib with extra functionality

## Usage
Use 

```shell
from spathlib import Path
```
instead of

```shell
from pathlib import Path
```

To gain access to additional functions on path instances such as:
* is_root: whether path or first existing parent is owned by root user
* write: write content to file with dynamic check of content type to determine correct format
* load: load content of path with yaml extension in yaml format
* save: write content of path with yaml extension in yaml format
* find: recursively find all paths under a path that match a condition
* ..

Or inherit from this class to define your own additional functionality
