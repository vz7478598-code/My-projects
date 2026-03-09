"""Тесты для модуля определения типа файла по магическим байтам."""

import os
import tempfile

import pytest

from parsers.file_detector import detect_file_type

# ── Реальные PDF-файлы ──────────────────────────────────────────────

REAL_PDFS = [
    r"D:\ВЫПИСКА СБЕР.pdf",
    r"D:\Жуков_В_А_о_движении_денежных_средств_ozonbank_document_25183854.pdf",
]


@pytest.mark.parametrize("pdf_path", REAL_PDFS)
def test_real_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        pytest.skip(f"Файл не найден: {pdf_path}")
    assert detect_file_type(pdf_path) == "pdf"


# ── Синтетические файлы ─────────────────────────────────────────────

def _write_tmp(data: bytes) -> str:
    f = tempfile.NamedTemporaryFile(delete=False)
    f.write(data)
    f.close()
    return f.name


def test_png_signature():
    path = _write_tmp(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
    try:
        assert detect_file_type(path) == "png"
    finally:
        os.unlink(path)


def test_jpeg_signature():
    path = _write_tmp(b'\xff\xd8\xff\xe0' + b'\x00' * 100)
    try:
        assert detect_file_type(path) == "jpeg"
    finally:
        os.unlink(path)


def test_pdf_signature():
    path = _write_tmp(b'%PDF-1.4 fake content')
    try:
        assert detect_file_type(path) == "pdf"
    finally:
        os.unlink(path)


def test_unknown_file():
    path = _write_tmp(b'This is a plain text file')
    try:
        assert detect_file_type(path) == "unknown"
    finally:
        os.unlink(path)


def test_empty_file():
    path = _write_tmp(b'')
    try:
        assert detect_file_type(path) == "unknown"
    finally:
        os.unlink(path)


def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        detect_file_type("nonexistent_file.xyz")
