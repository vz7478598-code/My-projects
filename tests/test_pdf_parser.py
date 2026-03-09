"""Тесты для parsers.pdf_parser (автономные, без внешних файлов)."""

import os
import tempfile

import pytest
from fpdf import FPDF

from parsers.pdf_parser import (
    check_pdf_integrity,
    extract_tables_from_pdf,
    extract_text_from_pdf,
)


@pytest.fixture
def valid_pdf(tmp_path):
    """Создаёт минимальный валидный PDF с латинским текстом."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(200, 10, text="Outgoing balance: 75 000,50 rub.")
    path = str(tmp_path / "valid.pdf")
    pdf.output(path)
    return path


@pytest.fixture
def text_rich_pdf(tmp_path):
    """Создаёт PDF с достаточным количеством текста (>50 символов без пробелов)."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    # Достаточно длинный текст чтобы пройти порог в 50 символов
    lines = [
        "Bank Statement for account 40817810099910004567",
        "Date: 2025-01-15",
        "Outgoing balance: 75 000,50 rub.",
        "Incoming transfer from OOO Roga i Kopyta: 150 000,00 rub.",
        "Payment for services: 25 300,75 rub.",
    ]
    for line in lines:
        pdf.cell(0, 10, text=line, new_x="LMARGIN", new_y="NEXT")
    path = str(tmp_path / "rich.pdf")
    pdf.output(path)
    return path


@pytest.fixture
def empty_pdf(tmp_path):
    """Создаёт PDF с пустой страницей (без текста)."""
    pdf = FPDF()
    pdf.add_page()
    path = str(tmp_path / "empty.pdf")
    pdf.output(path)
    return path


class TestCheckPdfIntegrity:
    def test_integrity_valid(self, valid_pdf):
        result = check_pdf_integrity(valid_pdf)
        assert result == {"ok": True}

    def test_integrity_missing(self):
        result = check_pdf_integrity("/nonexistent/path/missing.pdf")
        assert result["ok"] is False
        assert result["error_type"] == 2

    def test_integrity_corrupted(self, tmp_path):
        corrupted = str(tmp_path / "corrupted.pdf")
        with open(corrupted, "wb") as f:
            f.write(b"this is not a valid pdf file at all")
        result = check_pdf_integrity(corrupted)
        assert result["ok"] is False
        assert result["error_type"] == 2


class TestExtractTextFromPdf:
    def test_extract_text(self, text_rich_pdf):
        result = extract_text_from_pdf(text_rich_pdf)
        assert result["ok"] is True
        assert "text" in result
        assert "pages" in result
        assert result["pages"] >= 1
        assert "75 000,50" in result["text"]

    def test_extract_empty(self, empty_pdf):
        result = extract_text_from_pdf(empty_pdf)
        assert result["ok"] is False
        assert result["error_type"] == 3

    def test_extract_nonexistent(self):
        result = extract_text_from_pdf("/nonexistent/path/missing.pdf")
        assert result["ok"] is False
        assert result["error_type"] == 2


class TestExtractTablesFromPdf:
    def test_extract_tables_no_tables(self, text_rich_pdf):
        tables = extract_tables_from_pdf(text_rich_pdf)
        assert isinstance(tables, list)

    def test_extract_tables_empty_pdf(self, empty_pdf):
        tables = extract_tables_from_pdf(empty_pdf)
        assert tables == []
