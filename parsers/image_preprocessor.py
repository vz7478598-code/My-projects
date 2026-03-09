"""
Модуль предобработки изображений для OCR.

Конвейер: grayscale → масштабирование → шумоподавление → бинаризация → deskew.
Выход — PIL.Image, готовый для pytesseract.
"""

import os

import cv2
import numpy as np
from PIL import Image

MAX_FILE_SIZE_MB = 10
MAX_RESOLUTION = (8000, 8000)
MAX_PIXELS = 20_000_000
SUPPORTED_FORMATS = ("PNG", "JPEG")


def validate_image(file_path: str) -> dict:
    """
    Проверяет, что файл — корректное изображение в поддерживаемом формате.

    Возвращает:
        {"ok": True, "format": "PNG", "size_mb": 1.5, "resolution": (1920, 1080)}
        {"ok": False, "error_type": "...", "detail": "..."}
    """
    if not os.path.exists(file_path):
        return {
            "ok": False,
            "error_type": "file_not_found",
            "detail": f"Файл не найден: {file_path}",
        }

    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return {
            "ok": False,
            "error_type": "image_too_large",
            "detail": f"Размер файла {size_mb:.1f} МБ превышает лимит {MAX_FILE_SIZE_MB} МБ",
        }

    try:
        img = Image.open(file_path)
        img.verify()
    except (IOError, SyntaxError) as e:
        return {
            "ok": False,
            "error_type": "image_corrupted",
            "detail": f"Файл повреждён или не является изображением: {e}",
        }

    img = Image.open(file_path)
    fmt = img.format
    w, h = img.size

    if fmt not in SUPPORTED_FORMATS:
        return {
            "ok": False,
            "error_type": "unsupported_format",
            "detail": f"Формат {fmt} не поддерживается. Используйте PNG или JPG",
        }

    if w > MAX_RESOLUTION[0] or h > MAX_RESOLUTION[1]:
        return {
            "ok": False,
            "error_type": "image_too_large",
            "detail": f"Разрешение {w}x{h} превышает лимит {MAX_RESOLUTION[0]}x{MAX_RESOLUTION[1]}",
        }

    return {
        "ok": True,
        "format": fmt,
        "size_mb": round(size_mb, 1),
        "resolution": (w, h),
    }


def detect_skew_angle(binary_image: np.ndarray) -> float:
    """
    Определяет угол перекоса текста в градусах.
    Положительный — повернут по часовой стрелке.
    """
    coords = np.column_stack(np.where(binary_image < 128))
    if len(coords) < 100:
        return 0.0
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    return angle


def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
    """
    Поворачивает изображение на заданный угол с сохранением размера.
    """
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image,
        matrix,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return rotated


def preprocess_for_ocr(image_path: str) -> dict:
    """
    Полный конвейер предобработки изображения для OCR.

    Конвейер: grayscale → масштабирование → шумоподавление → бинаризация → deskew.

    Возвращает:
        {"ok": True, "image": PIL.Image, "steps_applied": [...]}
        {"ok": False, "error_type": "...", "detail": "..."}
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return {
                "ok": False,
                "error_type": "image_corrupted",
                "detail": "Не удалось открыть изображение",
            }

        h, w = img.shape[:2]
        steps = []

        if h * w > MAX_PIXELS:
            return {
                "ok": False,
                "error_type": "image_too_large",
                "detail": f"Разрешение {w}x{h} превышает лимит {MAX_PIXELS} пикселей",
            }

        # 1. Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        steps.append("grayscale")

        # 2. Масштабирование (если изображение маленькое)
        if h < 1000 or w < 1000:
            scale = 2.0
            gray = cv2.resize(
                gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC
            )
            steps.append(f"upscale_x{scale}")

        # 3. Шумоподавление
        denoised = cv2.medianBlur(gray, 3)
        steps.append("denoise_median")

        # 4. Адаптивная бинаризация
        binary = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=11,
            C=2,
        )
        steps.append("adaptive_threshold")

        # 5. Deskew
        angle = detect_skew_angle(binary)
        if abs(angle) > 0.5:
            binary = rotate_image(binary, angle)
            steps.append(f"deskew_{angle:.1f}deg")

        # Конвертация в PIL.Image
        pil_image = Image.fromarray(binary)

        return {"ok": True, "image": pil_image, "steps_applied": steps}

    except Exception as e:
        return {
            "ok": False,
            "error_type": "preprocess_error",
            "detail": str(e),
        }
