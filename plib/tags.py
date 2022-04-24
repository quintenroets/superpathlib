try:
    import xattr

except:
    xattr = None  # Don't fail if xattr not supported (Windows)

delim = ","
default_tag_name = "user.xdg.tags"

"""
More user-friendly way to interact with tags.
- Work with strings and integers instead of bytes
- Use xdg tags by default -> useful for filemanager that can order according to this tag
"""


class XDGTags:
    def __init__(self, path, name=default_tag_name):
        self.tags = xattr.xattr(path) if xattr is not None else None
        self.name = name

    def get(self):
        tags = set({})
        if self.tags and self.tags.has_key(self.name):
            tags = self.tags[self.name].decode().strip().split(delim)
        return tags

    def set(self, *values, name=default_tag_name):
        """
        :param values: tag values to set
        """
        if self.tags is not None:
            values = {str(v).zfill(4) if isinstance(v, int) else str(v) for v in values}
            values = delim.join(values).encode()
            self.tags.set(self.name, values)

    def clear(self):
        if self.tags is not None and self.tags.has_key(self.name):
            self.tags.remove(self.name)
