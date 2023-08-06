from __future__ import annotations

import json
import typing
from collections.abc import Iterable
from typing import Any

from . import base

if typing.TYPE_CHECKING:
    import numpy as np  # noqa: autoimport


# Long import times relative to usage frequency: lazy imports
# import yaml
# import numpy as np


class Path(base.Path):
    """
    Properties to read & write content in different formats.
    """

    @property
    def byte_content(self) -> bytes:
        return self.read_bytes()

    @byte_content.setter
    def byte_content(self, value: bytes) -> None:
        self.write_bytes(value)

    @property
    def text(self) -> str:
        return self.read_text()

    @text.setter
    def text(self, value: str | Any) -> None:
        self.write_text(str(value))

    @property
    def lines(self) -> list[str]:
        lines = self.text.strip().splitlines()
        lines = [line for line in lines if line]
        return lines

    @lines.setter
    def lines(self, lines: Iterable[Any]) -> None:
        self.text = "\n".join(str(line) for line in lines)

    @property
    def json(self) -> dict:
        return json.loads(self.text or "{}")

    @json.setter
    def json(self, content: dict):
        self.text = json.dumps(content)

    @property
    def yaml(self) -> dict:
        import yaml  # noqa: autoimport

        # C implementation much faster but only supported on Linux
        Loader = yaml.CFullLoader if hasattr(yaml, "CFullLoader") else yaml.FullLoader
        return yaml.load(self.text, Loader=Loader) or {}

    @yaml.setter
    def yaml(self, value: dict):
        import yaml  # noqa: autoimport

        # C implementation much faster but only supported on Linux
        Dumper = yaml.CDumper if hasattr(yaml, "CDumper") else yaml.Dumper
        self.text = yaml.dump(value, Dumper=Dumper, width=1024)

    @property
    def numpy(self) -> np.ndarray:
        import numpy as np  # noqa: autoimport

        with self.open("rb") as fp:
            return np.load(fp)  # noqa

    @numpy.setter
    def numpy(self, value: np.ndarray):
        import numpy as np  # noqa: autoimport

        with self.open("wb") as fp:
            np.save(fp, value)  # noqa
