"""Validate upload extensions, size and document structure."""

import warnings
from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader

MAX_FILE_SIZE = 2 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


class UploadValidationError(ValueError):
    """Raised when an uploaded file fails validation."""


def validate_pdf(content):
    if not content.startswith(b"%PDF-"):
        raise UploadValidationError(
            "The file content does not match its extension."
        )

    try:
        reader = PdfReader(BytesIO(content), strict=True)

        if reader.is_encrypted:
            raise UploadValidationError(
                "Password-protected PDFs are not supported."
            )

        if len(reader.pages) == 0:
            raise UploadValidationError(
                "The PDF must contain at least one page."
            )

        # Resolve every page and read its content streams.
        for page in reader.pages:
            contents = page.get_contents()
            if contents is not None:
                contents.get_data()

    except UploadValidationError:
        raise
    except Exception as exc:
        raise UploadValidationError(
            "The PDF is invalid or damaged."
        ) from exc


def validate_image(content, extension):
    expected_format = "PNG" if extension == ".png" else "JPEG"

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)

            with Image.open(BytesIO(content)) as image:
                if image.format != expected_format:
                    raise UploadValidationError(
                        "The file content does not match its extension."
                    )
                image.verify()

            # Reopen and decode the pixels after verification.
            with Image.open(BytesIO(content)) as image:
                image.load()

    except UploadValidationError:
        raise
    except (
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise UploadValidationError(
            "The image is invalid, damaged or too large to process."
        ) from exc


def validate_upload(upload):
    """Return (file_bytes, extension) after successful validation."""
    if upload is None or not upload.filename:
        raise UploadValidationError("Please select a file.")

    extension = Path(upload.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise UploadValidationError(
            "Only PDF, JPEG and PNG files are allowed."
        )

    upload.stream.seek(0)
    content = upload.stream.read(MAX_FILE_SIZE + 1)
    upload.stream.seek(0)

    if not content:
        raise UploadValidationError("The selected file is empty.")

    if len(content) > MAX_FILE_SIZE:
        raise UploadValidationError(
            "The file exceeds the 2 MB upload limit."
        )

    if extension == ".pdf":
        validate_pdf(content)
    else:
        validate_image(content, extension)

    return content, extension