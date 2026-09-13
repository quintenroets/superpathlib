import shutil
from functools import cached_property
from typing import Generic, TypeVar, cast

from .extra_functionality import Path

P = TypeVar("P", bound=Path)


class Archive(Generic[P]):
    def __init__(self, path: P) -> None:
        self.path = path

    @cached_property
    def format_(self) -> str | None:
        # noinspection PyProtectedMember
        format_ = shutil._find_unpack_format(str(self.path))  # type: ignore[attr-defined] # noqa: SLF001
        return cast("str | None", format_)

    def unpack(  # noqa: PLR0913
        self,
        extraction_directory: P | None = None,
        *,
        remove_existing: bool = True,
        preserve_mtime: bool = True,
        remove_original: bool = True,
        format_: str | None = None,
        recursive: bool = True,
    ) -> None:
        format_ = cast("str", self.format_) if format_ is None else format_
        extraction_directory = (
            self.create_extraction_directory(format_)
            if extraction_directory is None
            else extraction_directory
        )

        if remove_existing:
            extraction_directory.remove()

        shutil.unpack_archive(
            self.path,
            extract_dir=extraction_directory,
            format=format_,
        )

        self.cleanup(extraction_directory)
        if preserve_mtime:
            self.path.copy_mtime_to(extraction_directory)

        if remove_original:
            self.path.unlink()

        if recursive:
            for path in extraction_directory.find():
                path.unpack_if_archive()

    def create_extraction_directory(self, format_: str) -> P:
        # noinspection PyProtectedMember
        unpack_formats = shutil._UNPACK_FORMATS  # type: ignore[attr-defined] # noqa: SLF001
        extensions, *_ = unpack_formats[format_]
        extract_name = self.path.name
        for archive_extension in extensions:
            extract_name = extract_name.removesuffix(archive_extension)
        return self.path.with_name(extract_name)

    @staticmethod
    def cleanup(extraction_directory: P) -> None:
        (extraction_directory / "__MACOSX").rmtree(missing_ok=True)
        subfolder = extraction_directory / extraction_directory.name
        if subfolder.exists() and extraction_directory.number_of_children == 1:
            subfolder.pop_parent()  # pragma: nocover
