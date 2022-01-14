from plib import Path
import time

path = Path.docs / "test.txt"

with path:
    time.sleep(2)
