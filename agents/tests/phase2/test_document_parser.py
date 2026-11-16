
from pathlib import Path

from pymupdf import pymupdf
import pytest
from docx import Document

from services.document_parser import DocumentParser


@pytest.fixture
def parser():
    return DocumentParser()


def test_extract_txt(parser):
    file_path = Path(
        "sample_data/quotations/supplier_a.txt"
    )

    text = parser.extract_text(file_path)

    assert "ABC Technologies" in text
    assert "Enterprise Server" in text
    assert "75,000" in text


def test_extract_docx(parser, tmp_path):
    file_path = tmp_path / "sample.docx"

    document = Document()
    document.add_paragraph("Supplier: Test Technologies")

    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Product"
    table.cell(0, 1).text = "Server"

    document.save(file_path)

    text = parser.extract_text(file_path)

    assert "Test Technologies" in text
    assert "Server" in text


def test_extract_pdf(parser, tmp_path):
    file_path = tmp_path / "sample.pdf"

    document = pymupdf.open()
    page = document.new_page()

    page.insert_text(
        (72, 72),
        "Supplier: PDF Technologies"
    )

    document.save(file_path)
    document.close()

    text = parser.extract_text(file_path)

    assert "PDF Technologies" in text


def test_missing_file(parser):
    with pytest.raises(FileNotFoundError):
        parser.extract_text("missing.txt")


def test_unsupported_format(parser, tmp_path):
    file_path = tmp_path / "quotation.xlsx"
    file_path.write_text("Sample")

    with pytest.raises(ValueError):
        parser.extract_text(file_path)


def test_empty_file(parser, tmp_path):
    file_path = tmp_path / "empty.txt"
    file_path.write_text("   ")

    with pytest.raises(ValueError):
        parser.extract_text(file_path)
