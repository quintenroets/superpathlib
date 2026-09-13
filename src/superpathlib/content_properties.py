from __future__ import annotations

import typing
from typing import Any

from . import metadata_properties
from .utils import catch_missing

if typing.TYPE_CHECKING:  # pragma: nocover
    from collections.abc import Iterable

    from numpy.typing import NDArray


class Path(metadata_properties.Path):
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
    @catch_missing(default="")
    def text(self) -> str:
        return self.read_text()

    @text.setter
    def text(self, value: Any) -> None:
        self.write_text(str(value))

    @property
    def lines(self) -> list[str]:
        return self.text.splitlines()

    @lines.setter
    def lines(self, lines: Iterable[Any]) -> None:
        self.text = "\n".join(str(line) for line in lines)

    @property
    def content_lines(self) -> list[str]:
        return [line for line in self.lines if line]

    @content_lines.setter
    def content_lines(self, lines: Iterable[Any]) -> None:
        lines = (line for line in lines if line)
        self.lines = typing.cast("list[str]", lines)

    @property
    @catch_missing(default=None)
    def json(self) -> Any:
        with self.open("rb") as fp:
            import json

            return json.load(fp)

    @json.setter
    def json(self, content: Any) -> None:
        import json

        with self.open("w") as fp:
            json.dump(content, fp)

    @property
    @catch_missing(default=None)
    def yaml(self) -> Any:
        with self.open("rb") as fp:
            import yaml

            # C implementation much faster
            loader = yaml.CSafeLoader if yaml.__with_libyaml__ else yaml.SafeLoader
            return yaml.load(fp, Loader=loader)  # noqa: S506

    @yaml.setter
    def yaml(self, value: Any) -> None:
        import yaml

        # C implementation much faster
        dumper = yaml.CSafeDumper if yaml.__with_libyaml__ else yaml.SafeDumper
        with self.open("w") as fp:
            yaml.dump(value, fp, Dumper=dumper, width=1024)

    @property
    def cached_yaml(self) -> Any:
        cache_file = self.with_name(self.name + ".cache")
        mtime = self.mtime
        exists = mtime > 0
        if exists and cache_file.mtime != mtime:
            cache_file.json = self.yaml
            cache_file.mtime = mtime
        return cache_file.json if exists else None

    @property
    def numpy(self) -> NDArray[Any]:
        import numpy as np

        with self.open("rb") as fp:
            return np.load(fp)  # type: ignore[no-any-return]

    @numpy.setter
    def numpy(self, value: NDArray[Any]) -> None:
        import numpy as np

        with self.open("wb") as fp:
            np.save(fp, value)
