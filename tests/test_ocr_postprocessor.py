"""Tests for OCR post-processing module."""

import pytest

from parsers.ocr_postprocessor import postprocess_ocr_text


class TestPostprocessOcrText:

    def test_fix_amount(self):
        assert postprocess_ocr_text("\u22121 25О,ОО руб.") == "-1 250,00 руб."

    def test_fix_date(self):
        assert postprocess_ocr_text("О1.ОЗ.2024") == "01.03.2024"

    def test_multiple_spaces(self):
        assert postprocess_ocr_text("ПЯТЕРОЧКА     1250,00") == "ПЯТЕРОЧКА 1250,00"

    def test_multiple_newlines(self):
        assert postprocess_ocr_text("строка1\n\n\n\nстрока2") == "строка1\n\nстрока2"

    def test_clean_text_passthrough(self):
        assert postprocess_ocr_text("01.03.2024 ПЯТЕРОЧКА -1 250,00") == "01.03.2024 ПЯТЕРОЧКА -1 250,00"

    def test_combined(self):
        assert postprocess_ocr_text("О1.ОЗ.2024  ПЯТЕРОЧКА   -1 25О,ОО руб.") == "01.03.2024 ПЯТЕРОЧКА -1 250,00 руб."
