import pytesseract
from parsers.image_preprocessor import preprocess_for_ocr


def ocr_image(image_path: str) -> dict:
    try:
        result = preprocess_for_ocr(image_path)
        if not result["ok"]:
            raise RuntimeError(result.get("error", "Ошибка предобработки изображения"))

        image = result["image"]
        steps_applied = result.get("steps_applied", [])

        text = pytesseract.image_to_string(
            image, lang="rus+eng", config="--psm 6 --oem 1"
        )

        stripped = text.replace(" ", "").replace("\n", "").replace("\r", "")
        if len(stripped) < 50:
            return {
                "ok": False,
                "error_type": "ocr_empty",
                "detail": f"Распознано только {len(stripped)} символов",
            }

        return {"ok": True, "text": text, "steps_applied": steps_applied}

    except pytesseract.TesseractNotFoundError:
        return {
            "ok": False,
            "error_type": "ocr_not_installed",
            "detail": "Tesseract не найден",
        }
    except Exception as e:
        return {"ok": False, "error_type": "ocr_error", "detail": str(e)}


def ocr_with_confidence(image_path: str) -> dict:
    try:
        result = preprocess_for_ocr(image_path)
        if not result["ok"]:
            raise RuntimeError(result.get("error", "Ошибка предобработки изображения"))

        image = result["image"]

        data = pytesseract.image_to_data(
            image,
            lang="rus+eng",
            config="--psm 6 --oem 1",
            output_type=pytesseract.Output.DICT,
        )

        confidences = [int(c) for c in data["conf"] if int(c) > 0]
        words = [t for t, c in zip(data["text"], data["conf"]) if int(c) > 0 and t.strip()]

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        text = " ".join(words)

        return {
            "ok": True,
            "text": text,
            "avg_confidence": round(avg_confidence, 1),
            "word_count": len(words),
        }

    except pytesseract.TesseractNotFoundError:
        return {
            "ok": False,
            "error_type": "ocr_not_installed",
            "detail": "Tesseract не найден",
        }
    except Exception as e:
        return {"ok": False, "error_type": "ocr_error", "detail": str(e)}
