# Superpathlib
Superpathlib offers Path objects with functionality extended from pathlib to maximize your productivity with a minimal amount of code.

## Usage
Use 

```shell
from plib import Path
path = Path(filename)
```

1) Use properties to read & write path content in different formats
    * text
    * byte_content
    * lines
    * yaml
    * json
    
    example usage: 

        ```shell
        path.json = {key: value}
        
        for line in path.lines:
            if interesting(line):
                process(line)
        ```
2) Use properties to get and set file metadata
    * mtime: modified time
    * size: filesize
    * tag: can be used for alternative ordering or metadata
    * is_root: whether the owner of the file is a root user
    
    example usage: 

        ```shell
        path_new.mtime = path_old.mtime
        
        if path.tag != skip_keyword:
            process(path)
        ```
3) Use properties to access commonly used folders:
    * docs
    * assets
    * ..
    
    example usage: 

        ```shell
        names_path = Path.assets / 'names'
        names = names_path.lines
        ```
4) Use additional functionality
    * find(): recursively find all paths under a root that match a condition (extra options available for performance optimization)
    * rmtree(): remove directory recursively
    * copy_to(): copy content to new file
    * tempfile(): create temporary file that can be used as context manager
    
    example usage: 

        ```shell
        with Path.tempfile() as tmp:
            do_work(logfile=tmp)
            log = tmp.text
        process(log)
        
        condition = lambda p: (p / '.git').exists()
        for git_path in root.find(condition):
            process_git(git_path)
        ```
5) Enhance existing functionality
    * Automatically create parents when writing files, creating new files, renaming files, ..
    * Return default values when path does not exist (e.g. size = 0, lines=[])
6) Inherit from this class to define your own additional functionality:

    example usage: 

        ```shell
        from plib import Path as BasePath

        class Path(BasePath):
            def count_children(self):
                return len(list(self.iterdir()))
        ```

        This only works for inheritance from plib and not from pathlib


## Installation

```shell
pip install git+https://github.com/quintenroets/superpathlib
```
