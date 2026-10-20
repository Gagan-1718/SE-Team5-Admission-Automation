"""Replacement validation and private storage must preserve the original file."""

from io import BytesIO
from pathlib import Path

import pytest
from pypdf import PdfWriter
from werkzeug.datastructures import FileStorage

from app.documents.storage import save_replacement_file, stored_file_path


def pdf_upload():
    stream = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(stream)
    stream.seek(0)
    return FileStorage(stream=stream, filename="replacement.pdf")


@pytest.fixture
def directory(app, tmp_path):
    directory = tmp_path / "private-uploads"
    directory.mkdir()
    app.config["DOCUMENT_UPLOAD_DIR"] = str(directory)
    return directory


def test_replacement_gets_unique_name_without_overwriting_original(directory):
    original = directory / "original.pdf"
    original.write_bytes(b"original content")
    first = save_replacement_file(pdf_upload())
    second = save_replacement_file(pdf_upload())
    assert first != second
    assert first != "replacement.pdf"
    assert stored_file_path(first).read_bytes().startswith(b"%PDF-")
    assert original.read_bytes() == b"original content"


def test_invalid_replacement_creates_no_file(directory):
    invalid = FileStorage(stream=BytesIO(b"MZ disguised executable"), filename="bad.pdf")
    with pytest.raises(ValueError):
        save_replacement_file(invalid)
    assert list(directory.iterdir()) == []


@pytest.mark.parametrize("name", ["../secret.pdf", "..\\secret.pdf", "C:secret.pdf", "", ".", "..", None])
def test_stored_path_rejects_unsafe_names(directory, name):
    with pytest.raises(ValueError):
        stored_file_path(name)


def test_partial_write_is_cleaned_up(directory, monkeypatch):
    real_open = Path.open

    class BrokenOutput:
        def __init__(self, output):
            self.output = output

        def __enter__(self):
            return self

        def write(self, content):
            self.output.write(content[:10])
            raise OSError("Simulated disk failure")

        def __exit__(self, *args):
            self.output.close()

    def broken_open(path, mode="r", *args, **kwargs):
        output = real_open(path, mode, *args, **kwargs)
        return BrokenOutput(output) if mode == "xb" else output

    monkeypatch.setattr(Path, "open", broken_open)
    with pytest.raises(OSError, match="Simulated disk failure"):
        save_replacement_file(pdf_upload())
    assert list(directory.iterdir()) == []
