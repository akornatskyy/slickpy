import typing
from asyncio import get_running_loop
from tempfile import SpooledTemporaryFile

try:
    from python_multipart.multipart import (
        MultipartParser,
        parse_options_header,
    )
except ImportError:  # pragma: nocover
    parse_options_header = None

from slickpy.typing import FormParams, MultipartFile, MultipartFiles


class MultipartFileWriter:
    roll_size = 1024 * 1024

    def __init__(self, name: str, content_type: str) -> None:
        self.name = name
        self.content_type = content_type
        self.size = 0
        # closed by MultipartFile.close()
        self.file = SpooledTemporaryFile(  # noqa: SIM115
            max_size=self.roll_size
        )

    def would_roll(self, size: int) -> bool:
        return self.size + size >= self.roll_size

    def write(self, chunk: bytes) -> int:
        ws = self.file.write(chunk)
        self.size += ws
        return ws

    def seek(self) -> int:
        return self.file.seek(0)


Operations = list[tuple[MultipartFileWriter, bytes | None]]


async def parse_multipart(  # noqa: C901, CCR001
    content_type_header: bytes, chunks: typing.AsyncIterator[bytes]
) -> tuple[FormParams, MultipartFiles]:
    assert (
        parse_options_header is not None
    ), "The 'python-multipart' package must be installed."
    content_type, params = parse_options_header(content_type_header)
    header_field = b""
    header_value = b""
    content_disposition = b""
    field_name = ""
    field_value = b""
    mfw: MultipartFileWriter | None = None

    io_pending: Operations = []
    form: list[tuple[str, str]] = []
    files: list[tuple[str, MultipartFile]] = []

    def callback(  # noqa: CCR001
        name: str,
        data: bytes | None = None,
        start: int | None = None,
        end: int | None = None,
    ) -> None:
        nonlocal header_field, header_value, content_disposition, content_type
        nonlocal field_name, field_value, mfw
        if name == "header_field":
            header_field += data[start:end]  # type: ignore[index]
        elif name == "header_value":
            header_value += data[start:end]  # type: ignore[index]
        elif name == "header_end":
            f = header_field.lower()
            if f == b"content-disposition":
                content_disposition = header_value
            elif f == b"content-type":
                content_type = header_value
            header_field = b""
            header_value = b""
        elif name == "headers_finished":
            _disposition, options = parse_options_header(content_disposition)
            field_name = options[b"name"].decode("utf-8")
            field_value = b""
            if b"filename" in options:
                mfw = MultipartFileWriter(
                    options[b"filename"].decode("utf-8"),
                    content_type.decode("utf-8"),
                )
            else:
                mfw = None
        elif name == "part_data":
            if mfw:
                chunk = data[start:end]  # type: ignore[index]
                if mfw.would_roll(len(chunk)):
                    io_pending.append((mfw, chunk))
                else:
                    mfw.write(chunk)
            else:
                field_value += data[start:end]  # type: ignore[index]
        elif name == "part_end":
            if mfw:
                rolled = mfw.would_roll(0)
                if rolled:
                    io_pending.append((mfw, None))
                else:
                    mfw.seek()
                files.append(
                    (
                        field_name,
                        MultipartFile(
                            mfw.name, mfw.content_type, rolled, mfw.file
                        ),
                    )
                )
            else:
                form.append((field_name, field_value.decode("utf-8")))

    parser = MultipartParser(params.get(b"boundary"))
    parser.callback = callback

    loop = get_running_loop()
    async for chunk in chunks:
        parser.write(chunk)
        if io_pending:
            await loop.run_in_executor(None, flush_pending_io, io_pending)
            io_pending.clear()

    return FormParams(form), MultipartFiles(files)


def flush_pending_io(operations: Operations) -> None:
    for mf, data in operations:
        if data is None:
            mf.seek()
        else:
            mf.write(data)
