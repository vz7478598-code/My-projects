"""
OCR-движок: распознавание текста с изображений банковских выписок.

Конвейер: validate → preprocess_for_ocr → pytesseract → postprocess.
"""

import pytesseract
from PIL import Image

from parsers.image_preprocessor import preprocess_for_ocr, validate_image
from parsers.ocr_postprocessor import clean_ocr_text

# Путь к Tesseract (Windows)
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

TESSERACT_CONFIG = "--psm 6 --oem 1"
TESSERACT_LANG = "rus+eng"
MIN_TEXT_LENGTH = 50


def ocr_image(image_path: str) -> dict:
    """
    Распознаёт текст с изображения банковской выписки.

    Конвейер:
    1. Валидация файла (формат, размер)
    2. Предобработка (grayscale, бинаризация, deskew)
    3. OCR через Tesseract (rus+eng)
    4. Постобработка (исправление OCR-ошибок)

    Возвращает:
        {"ok": True, "text": "...", "confidence": 85.5}
        {"ok": False, "error_type": "...", "detail": "..."}
    """
    # 1. Валидация
    validation = validate_image(image_path)
    if not validation["ok"]:
        return validation

    # 2. Предобработка
    preprocess_result = preprocess_for_ocr(image_path)
    if not preprocess_result["ok"]:
        return preprocess_result

    processed_image: Image.Image = preprocess_result["image"]

    # 3. OCR
    try:
        raw_text = pytesseract.image_to_string(
            processed_image,
            lang=TESSERACT_LANG,
            config=TESSERACT_CONFIG,
        )
    except pytesseract.TesseractNotFoundError:
        return {
            "ok": False,
            "error_type": "ocr_not_installed",
            "detail": "Tesseract не найден. Проверьте установку.",
        }
    except Exception as e:
        return {"ok": False, "error_type": "ocr_error", "detail": str(e)}

    # 4. Постобработка
    text = clean_ocr_text(raw_text)

    # Проверка минимальной длины
    cleaned = text.replace(" ", "").replace("\n", "")
    if len(cleaned) < MIN_TEXT_LENGTH:
        return {
            "ok": False,
            "error_type": "ocr_empty",
            "detail": f"Распознано только {len(cleaned)} символов",
        }

    # 5. Уверенность
    confidence = _compute_confidence(processed_image)

    return {"ok": True, "text": text, "confidence": confidence}


def _compute_confidence(image: Image.Image) -> float:
    """Вычисляет среднюю уверенность OCR (0-100)."""
    try:
        data = pytesseract.image_to_data(
            image,
            lang=TESSERACT_LANG,
            config=TESSERACT_CONFIG,
            output_type=pytesseract.Output.DICT,
        )
        confidences = [c for c in data["conf"] if c > 0]
        if not confidences:
            return 0.0
        return round(sum(confidences) / len(confidences), 1)
    except Exception:
        return 0.0
