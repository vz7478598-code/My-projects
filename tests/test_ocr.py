"""Тесты для OCR-модулей: ocr_postprocessor и ocr_engine."""

from unittest.mock import MagicMock, patch

import pytest

from parsers.ocr_postprocessor import clean_ocr_text


# ── clean_ocr_text ──


class TestCleanOcrText:
    def test_fix_cyrillic_O_in_date(self):
        # О1.ОЗ.2024 → 01.03.2024
        raw = "\u041e1.\u041eЗ.2024 Покупка"
        result = clean_ocr_text(raw)
        assert "01.03.2024" in result

    def test_fix_cyrillic_in_amount(self):
        # 25О,ОО → 250,00
        raw = "ПЯТЕРОЧКА -1 25\u041e,\u041e\u041e руб."
        result = clean_ocr_text(raw)
        assert "250,00" in result

    def test_collapse_multiple_spaces(self):
        raw = "Дата     Описание      Сумма"
        result = clean_ocr_text(raw)
        assert "  " not in result

    def test_collapse_multiple_blank_lines(self):
        raw = "Строка 1\n\n\n\n\nСтрока 2"
        result = clean_ocr_text(raw)
        assert "\n\n\n" not in result
        assert "Строка 1" in result
        assert "Строка 2" in result

    def test_preserves_valid_text(self):
        raw = "01.03.2024 ПЯТЕРОЧКА"
        result = clean_ocr_text(raw)
        assert result == raw

    def test_empty_string(self):
        assert clean_ocr_text("") == ""


# ── ocr_image ──


class TestOcrImage:
    @patch("parsers.ocr_engine.pytesseract")
    @patch("parsers.ocr_engine.preprocess_for_ocr")
    @patch("parsers.ocr_engine.validate_image")
    def test_success(self, mock_validate, mock_preprocess, mock_tess):
        mock_validate.return_value = {
            "ok": True,
            "format": "PNG",
            "size_mb": 1.0,
            "resolution": (1920, 1080),
        }

        fake_image = MagicMock()
        mock_preprocess.return_value = {
            "ok": True,
            "image": fake_image,
            "steps_applied": ["grayscale"],
        }

        ocr_text = (
            "ПАО Сбербанк\n"
            "Выписка по счёту 40817810000000000001\n"
            "01.03.2024 ПЯТЕРОЧКА -1 250,00\n"
            "Исходящий остаток: 75 000,50 руб."
        )
        mock_tess.image_to_string.return_value = ocr_text
        mock_tess.image_to_data.return_value = {"conf": [90, 85, 92, 88]}
        mock_tess.Output.DICT = "dict"

        from parsers.ocr_engine import ocr_image

        result = ocr_image("test.png")

        assert result["ok"] is True
        assert "Сбербанк" in result["text"]
        assert result["confidence"] > 0

    @patch("parsers.ocr_engine.validate_image")
    def test_validation_failure(self, mock_validate):
        mock_validate.return_value = {
            "ok": False,
            "error_type": "file_not_found",
            "detail": "Файл не найден",
        }

        from parsers.ocr_engine import ocr_image

        result = ocr_image("nonexistent.png")
        assert result["ok"] is False
        assert result["error_type"] == "file_not_found"

    @patch("parsers.ocr_engine.pytesseract")
    @patch("parsers.ocr_engine.preprocess_for_ocr")
    @patch("parsers.ocr_engine.validate_image")
    def test_empty_ocr_result(self, mock_validate, mock_preprocess, mock_tess):
        mock_validate.return_value = {
            "ok": True,
            "format": "PNG",
            "size_mb": 1.0,
            "resolution": (800, 600),
        }
        mock_preprocess.return_value = {
            "ok": True,
            "image": MagicMock(),
            "steps_applied": [],
        }
        mock_tess.image_to_string.return_value = "abc"
        mock_tess.Output.DICT = "dict"

        from parsers.ocr_engine import ocr_image

        result = ocr_image("empty.png")
        assert result["ok"] is False
        assert result["error_type"] == "ocr_empty"

    @patch("parsers.ocr_engine.preprocess_for_ocr")
    @patch("parsers.ocr_engine.validate_image")
    def test_preprocess_failure(self, mock_validate, mock_preprocess):
        mock_validate.return_value = {
            "ok": True,
            "format": "PNG",
            "size_mb": 1.0,
            "resolution": (800, 600),
        }
        mock_preprocess.return_value = {
            "ok": False,
            "error_type": "image_corrupted",
            "detail": "Не удалось открыть",
        }

        from parsers.ocr_engine import ocr_image

        result = ocr_image("corrupted.png")
        assert result["ok"] is False
        assert result["error_type"] == "image_corrupted"
