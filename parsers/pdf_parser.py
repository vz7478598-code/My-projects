"""Извлечение текста и таблиц из PDF-выписок банков."""

import PyPDF2
import pdfplumber


def check_pdf_integrity(file_path: str) -> dict:
    """Проверяет целостность PDF и наличие пароля.

    Args:
        file_path: путь к PDF-файлу.

    Returns:
        {"ok": True} — файл валиден.
        {"ok": False, "error_type": 2, "detail": "..."} — повреждён или защищён.
    """
    try:
        reader = PyPDF2.PdfReader(file_path)
        if reader.is_encrypted:
            return {"ok": False, "error_type": 2, "detail": "PDF защищён паролем"}
        _ = len(reader.pages)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error_type": 2, "detail": str(e)}


def extract_text_from_pdf(file_path: str) -> dict:
    """Извлекает текст со всех страниц PDF.

    Args:
        file_path: путь к PDF-файлу.

    Returns:
        {"ok": True, "text": "...", "pages": N} — текст извлечён.
        {"ok": False, "error_type": 3, "detail": "..."} — слишком мало текста.
        {"ok": False, "error_type": 2, "detail": "..."} — ошибка чтения.
    """
    try:
        full_text = ""
        with pdfplumber.open(file_path) as pdf:
            page_count = len(pdf.pages)
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"

        cleaned = full_text.replace(" ", "").replace("\n", "")
        if len(cleaned) < 50:
            return {
                "ok": False,
                "error_type": 3,
                "detail": f"Извлечено только {len(cleaned)} символов",
            }

        return {"ok": True, "text": full_text, "pages": page_count}

    except Exception as e:
        return {"ok": False, "error_type": 2, "detail": str(e)}


def extract_tables_from_pdf(file_path: str) -> list:
    """Извлекает таблицы со всех страниц PDF.

    Args:
        file_path: путь к PDF-файлу.

    Returns:
        Список таблиц. Каждая таблица — список строк, каждая строка — список ячеек.
    """
    tables = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            if page_tables:
                tables.extend(page_tables)
    return tables
