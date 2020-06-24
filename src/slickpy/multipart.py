import typing
from tempfile import SpooledTemporaryFile

from multipart import MultipartParser  # type: ignore[import]
from multipart.multipart import parse_options_header  # type: ignore[import]

from slickpy.comp import get_running_loop
from slickpy.typing import FormParams, MultipartFile, MultipartFiles


class MultipartFileWriter(object):
    # roll_size = 1
    roll_size = 1024 * 1024

    def __init__(self, name: str, content_type: str) -> None:
        self.name = name
        self.content_type = content_type
        self.size = 0
        self.file = SpooledTemporaryFile(max_size=self.roll_size)

    def would_roll(self, size: int) -> bool:
        return self.size + size >= self.roll_size

    def write(self, chunk: bytes) -> int:
        ws = self.file.write(chunk)
        self.size += ws
        return ws

    def seek(self) -> int:
        return self.file.seek(0)


Operations = typing.List[
    typing.Tuple[MultipartFileWriter, typing.Optional[bytes]]
]


async def parse_multipart(  # noqa: C901
    content_type_header: bytes, chunks: typing.AsyncIterator[bytes]
) -> typing.Tuple[FormParams, MultipartFiles]:
    content_type, params = parse_options_header(content_type_header)
    header_field = b""
    header_value = b""
    content_disposition = b""
    field_name = ""
    field_value = b""
    mfw: typing.Optional[MultipartFileWriter] = None

    io_pending: Operations = []
    form: typing.List[typing.Tuple[str, str]] = []
    files: typing.List[typing.Tuple[str, MultipartFile]] = []

    def callback(
        name: str,
        data: typing.Optional[bytes] = None,
        start: typing.Optional[int] = None,
        end: typing.Optional[int] = None,
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
            disposition, options = parse_options_header(content_disposition)
            field_name = options[b"name"].decode("utf-8")
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
    for (mf, data) in operations:
        if data is None:
            mf.seek()
        else:
            mf.write(data)
