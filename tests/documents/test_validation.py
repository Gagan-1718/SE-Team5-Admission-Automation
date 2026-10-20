from io import BytesIO

import pytest
from PIL import Image
from pypdf import PdfWriter
from werkzeug.datastructures import FileStorage

from app.documents.validation import (
    MAX_FILE_SIZE,
    UploadValidationError,
    validate_upload,
)


def pdf_bytes():
    output = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(output)
    return output.getvalue()


def image_bytes(image_format):
    output = BytesIO()
    with Image.new("RGB", (10, 10), color="white") as image:
        image.save(output, format=image_format)
    return output.getvalue()


def make_upload(filename, content):
    return FileStorage(
        stream=BytesIO(content),
        filename=filename,
    )


@pytest.mark.parametrize(
    "filename,content",
    [
        ("sample.pdf", pdf_bytes()),
        ("sample.jpg", image_bytes("JPEG")),
        ("sample.jpeg", image_bytes("JPEG")),
        ("sample.png", image_bytes("PNG")),
    ],
)
def test_valid_document_is_accepted(filename, content):
    upload = make_upload(filename, content)

    result, extension = validate_upload(upload)

    assert result == content
    assert extension == "." + filename.rsplit(".", 1)[1]
    assert upload.stream.tell() == 0


@pytest.mark.parametrize(
    "upload",
    [None, make_upload("", b"content")],
)
def test_missing_file_is_rejected(upload):
    with pytest.raises(UploadValidationError, match="select a file"):
        validate_upload(upload)


def test_empty_file_is_rejected():
    with pytest.raises(UploadValidationError, match="empty"):
        validate_upload(make_upload("empty.pdf", b""))


def test_unsupported_extension_is_rejected():
    with pytest.raises(UploadValidationError, match="Only PDF"):
        validate_upload(make_upload("program.exe", b"MZcontent"))


def test_disguised_file_is_rejected():
    with pytest.raises(UploadValidationError, match="does not match"):
        validate_upload(make_upload("program.pdf", b"MZcontent"))


@pytest.mark.parametrize(
    "filename,content",
    [
        ("broken.pdf", b"%PDF-test"),
        ("broken.jpg", b"\xff\xd8\xfftest"),
        ("broken.png", b"\x89PNG\r\n\x1a\ntest"),
    ],
)
def test_malformed_document_is_rejected(filename, content):
    with pytest.raises(UploadValidationError):
        validate_upload(make_upload(filename, content))


def test_image_format_must_match_extension():
    with pytest.raises(UploadValidationError, match="does not match"):
        validate_upload(
            make_upload("wrong.png", image_bytes("JPEG"))
        )


@pytest.mark.parametrize("size", [MAX_FILE_SIZE - 1, MAX_FILE_SIZE])
def test_valid_pdf_at_or_below_limit_is_accepted(size):
    content = pdf_bytes()

    # Insert whitespace before the final EOF marker without changing
    # the existing PDF object offsets.
    marker = content.rfind(b"%%EOF")
    padding = b" " * (size - len(content))
    content = content[:marker] + padding + content[marker:]

    result, _ = validate_upload(make_upload("boundary.pdf", content))

    assert len(result) == size


def test_oversized_file_is_rejected():
    content = b"%PDF-" + b"x" * (MAX_FILE_SIZE + 1 - 5)

    with pytest.raises(UploadValidationError, match="exceeds"):
        validate_upload(make_upload("large.pdf", content))


def test_uppercase_extension_is_accepted():
    _, extension = validate_upload(
        make_upload("sample.PDF", pdf_bytes())
    )

    assert extension == ".pdf"