from __future__ import annotations

try:
    import xattr

except ModuleNotFoundError:  # pragma: nocover
    # Don't fail if xattr not supported (Windows)
    xattr = None

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .metadata_properties import Path  # pragma: nocover

delim = ","
default_tag_name = "user.xdg.tags"


class XDGTags:
    """More user-friendly way to interact with tags.

    - Work with strings and integers instead of bytes
    - Use xdg tags by default ->
        useful for filemanager that can order according to this tag
    """

    def __init__(self, path: Path, name: str = default_tag_name) -> None:
        self.tags = xattr.xattr(path) if xattr is not None else None
        self.name = name

    def get(self) -> list[str]:
        tags = []
        if self.tags and self.tags.has_key(self.name):
            tags = self.tags[self.name].decode().strip().split(delim)
        return tags

    def set(self, *values: str | int | None) -> None:
        """
        :param values: tag values to set
        """
        if self.tags is not None:
            values_set = {
                str(v).zfill(4) if isinstance(v, int) else str(v)
                for v in values
                if v is not None
            }
            values_str = delim.join(values_set).encode()
            self.tags.set(self.name, values_str)

    def clear(self) -> None:
        if self.tags is not None and self.tags.has_key(self.name):
            self.tags.remove(self.name)
