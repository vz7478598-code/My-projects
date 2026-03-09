import unittest
from unittest.mock import patch, MagicMock

import pytesseract

from parsers.ocr_engine import ocr_image, ocr_with_confidence


def _fake_preprocess_ok():
    fake_image = MagicMock(name="FakePILImage")
    return {"ok": True, "image": fake_image, "steps_applied": ["grayscale", "threshold"]}


def _fake_preprocess_fail():
    return {"ok": False, "error": "Файл не найден"}


LONG_TEXT = (
    "Операция по счёту №1234567890 от 01.01.2025. "
    "Сумма: 15 000,00 руб. Назначение платежа: оплата услуг связи. "
    "Получатель: ООО Ростелеком. БИК 044525225. "
    "Корреспондентский счёт 30101810400000000225."
)


class TestOcrImage(unittest.TestCase):

    @patch("parsers.ocr_engine.preprocess_for_ocr")
    @patch("parsers.ocr_engine.pytesseract.image_to_string")
    def test_ocr_success(self, mock_ocr, mock_preprocess):
        mock_preprocess.return_value = _fake_preprocess_ok()
        mock_ocr.return_value = LONG_TEXT

        result = ocr_image("test.png")

        self.assertTrue(result["ok"])
        self.assertEqual(result["text"], LONG_TEXT)
        self.assertIn("grayscale", result["steps_applied"])
        mock_ocr.assert_called_once()

    @patch("parsers.ocr_engine.preprocess_for_ocr")
    @patch("parsers.ocr_engine.pytesseract.image_to_string")
    def test_ocr_empty(self, mock_ocr, mock_preprocess):
        mock_preprocess.return_value = _fake_preprocess_ok()
        mock_ocr.return_value = ""

        result = ocr_image("test.png")

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_type"], "ocr_empty")
        self.assertIn("0 символов", result["detail"])

    @patch("parsers.ocr_engine.preprocess_for_ocr")
    @patch("parsers.ocr_engine.pytesseract.image_to_string")
    def test_ocr_short_text(self, mock_ocr, mock_preprocess):
        mock_preprocess.return_value = _fake_preprocess_ok()
        mock_ocr.return_value = "Короткий текст"

        result = ocr_image("test.png")

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_type"], "ocr_empty")

    @patch("parsers.ocr_engine.preprocess_for_ocr")
    @patch("parsers.ocr_engine.pytesseract.image_to_string")
    def test_ocr_not_installed(self, mock_ocr, mock_preprocess):
        mock_preprocess.return_value = _fake_preprocess_ok()
        mock_ocr.side_effect = pytesseract.TesseractNotFoundError()

        result = ocr_image("test.png")

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_type"], "ocr_not_installed")
        self.assertIn("Tesseract не найден", result["detail"])

    @patch("parsers.ocr_engine.preprocess_for_ocr")
    def test_ocr_preprocess_failure(self, mock_preprocess):
        mock_preprocess.return_value = _fake_preprocess_fail()

        result = ocr_image("test.png")

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_type"], "ocr_error")


class TestOcrWithConfidence(unittest.TestCase):

    @patch("parsers.ocr_engine.preprocess_for_ocr")
    @patch("parsers.ocr_engine.pytesseract.image_to_data")
    def test_confidence_success(self, mock_data, mock_preprocess):
        mock_preprocess.return_value = _fake_preprocess_ok()
        mock_data.return_value = {
            "text": ["Сумма", "15000", "руб", "", ""],
            "conf": [95, 88, 91, -1, -1],
        }

        result = ocr_with_confidence("test.png")

        self.assertTrue(result["ok"])
        self.assertEqual(result["word_count"], 3)
        self.assertAlmostEqual(result["avg_confidence"], 91.3, places=1)
        self.assertIn("Сумма", result["text"])

    @patch("parsers.ocr_engine.preprocess_for_ocr")
    @patch("parsers.ocr_engine.pytesseract.image_to_data")
    def test_confidence_not_installed(self, mock_data, mock_preprocess):
        mock_preprocess.return_value = _fake_preprocess_ok()
        mock_data.side_effect = pytesseract.TesseractNotFoundError()

        result = ocr_with_confidence("test.png")

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_type"], "ocr_not_installed")


if __name__ == "__main__":
    unittest.main()
