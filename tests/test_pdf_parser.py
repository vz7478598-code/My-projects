"""Тесты для parsers.pdf_parser."""

import os
import tempfile

import pytest

from parsers.pdf_parser import check_pdf_integrity, extract_text_from_pdf

# Реальные PDF для интеграционных тестов
OZON_PDF = r"D:\Жуков_В_А_о_движении_денежных_средств_ozonbank_document_25183854.pdf"
SBER_PDF = r"D:\ВЫПИСКА СБЕР.pdf"


class TestCheckPdfIntegrity:
    def test_valid_pdf(self):
        result = check_pdf_integrity(OZON_PDF)
        assert result["ok"] is True

    def test_valid_pdf_sber(self):
        result = check_pdf_integrity(SBER_PDF)
        assert result["ok"] is True

    def test_nonexistent_file(self):
        result = check_pdf_integrity("nonexistent.pdf")
        assert result["ok"] is False
        assert result["error_type"] == 2

    def test_corrupted_file(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"not a pdf content")
            tmp_path = f.name
        try:
            result = check_pdf_integrity(tmp_path)
            assert result["ok"] is False
            assert result["error_type"] == 2
        finally:
            os.unlink(tmp_path)


class TestExtractTextFromPdf:
    def test_extract_ozon(self):
        result = extract_text_from_pdf(OZON_PDF)
        assert result["ok"] is True
        assert result["pages"] > 0
        assert len(result["text"]) > 100

    def test_extract_sber(self):
        result = extract_text_from_pdf(SBER_PDF)
        assert result["ok"] is True
        assert result["pages"] > 0
        assert len(result["text"]) > 100

    def test_nonexistent_file(self):
        result = extract_text_from_pdf("nonexistent.pdf")
        assert result["ok"] is False
        assert result["error_type"] == 2

    def test_corrupted_file(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"not a pdf content")
            tmp_path = f.name
        try:
            result = extract_text_from_pdf(tmp_path)
            assert result["ok"] is False
        finally:
            os.unlink(tmp_path)
