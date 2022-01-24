import time

from plib import Path

path = Path.docs / "test.txt"

with path.with_suffix(".yaml") as temp_path:
    print(temp_path)
    time.sleep(2)
