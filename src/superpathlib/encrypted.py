import io
import subprocess
from functools import cache
from types import TracebackType
from typing import IO, Any, cast

from package_utils.secrets_ import load_secret

from .path import Path


class EncryptedPath(Path):
    def open(  # type: ignore[override]
        self,
        mode: str = "r",
        buffering: int = -1,  # noqa: ARG002
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> IO[Any]:
        access = mode.replace("b", "").replace("t", "")
        writing = {"r": False, "w": True}[access]
        buffer = EncryptedFile(Path(self), writing=writing)
        return (
            buffer
            if "b" in mode
            else EncryptedTextFile(buffer, encoding, errors, newline)
        )


class EncryptedFile(io.BytesIO):
    def __init__(self, path: Path, *, writing: bool) -> None:
        self.path = path
        self.writing = writing
        plaintext = b"" if writing else run_gpg(path.read_bytes(), "--decrypt")
        super().__init__(plaintext)

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.cancel_write_if_failed(exception_type)
        super().__exit__(exception_type, exception, traceback)

    def cancel_write_if_failed(
        self,
        exception_type: type[BaseException] | None,
    ) -> None:
        self.writing &= exception_type is None

    def close(self) -> None:
        if not self.closed and self.writing:
            self.path.write_bytes(run_gpg(self.getvalue(), "--symmetric"))
        super().close()


class EncryptedTextFile(io.TextIOWrapper):
    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        cast("EncryptedFile", self.buffer).cancel_write_if_failed(exception_type)
        super().__exit__(exception_type, exception, traceback)


def run_gpg(data: bytes, *options: str) -> bytes:
    command = ("gpg", "--passphrase-fd", "0", "--batch", "--quiet", *options)
    input_ = f"{load_passphrase()}\n".encode() + data
    process = subprocess.run(command, input=input_, stdout=subprocess.PIPE, check=True)  # noqa: S603
    return process.stdout


@cache
def load_passphrase() -> str:
    return load_secret("file encryption password")
