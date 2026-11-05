"""Fictional specimen documents drawn for the demo dataset (R1-2)."""
from io import BytesIO

import pytest
from pypdf import PdfReader

from scripts.demo_documents import BUILDERS, render_pdf

INFO = {"name": "Fictional Person", "number": 7, "board": "CBSE", "percentage": 81.5,
        "category": "OBC", "city": "Udupi"}


@pytest.mark.parametrize("slug", sorted(BUILDERS))
def test_each_document_is_a_one_page_pdf_with_a_drawn_page(slug):
    data = render_pdf(slug, INFO)
    reader = PdfReader(BytesIO(data))
    assert len(reader.pages) == 1
    assert "Fictional specimen" in reader.metadata.title
    assert reader.pages[0].images  # a real drawn page, not an empty one
    assert len(data) > 20_000


def test_rejected_copy_is_different_from_the_clear_copy():
    assert render_pdf("marksheet", INFO, blurred=True) != render_pdf("marksheet", INFO)


def test_documents_carry_the_candidates_details():
    image = BUILDERS["marksheet"](INFO)
    assert image.size == (1190, 1684)
    other = BUILDERS["marksheet"](dict(INFO, name="Another Person"))
    assert image.tobytes() != other.tobytes()
