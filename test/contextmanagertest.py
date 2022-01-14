from plib import Path
import time

path = Path.docs / "test.txt"

with path.with_suffix(".yaml") as temp_path:
    print(temp_path)
    time.sleep(2)
