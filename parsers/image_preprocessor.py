import os

import cv2
import numpy as np
from PIL import Image

MAX_FILE_SIZE_MB = 10
MAX_RESOLUTION = 8000
MAX_PIXEL_COUNT = 20_000_000
SUPPORTED_FORMATS = {"PNG", "JPEG"}


def validate_image(file_path: str) -> dict:
    file_size = os.path.getsize(file_path)
    size_mb = file_size / (1024 * 1024)

    if size_mb > MAX_FILE_SIZE_MB:
        return {
            "ok": False,
            "error_type": "image_too_large",
            "detail": f"File size {size_mb:.1f} MB exceeds maximum {MAX_FILE_SIZE_MB} MB",
        }

    try:
        img = Image.open(file_path)
        img.verify()
    except Exception as e:
        return {
            "ok": False,
            "error_type": "image_corrupted",
            "detail": str(e),
        }

    img = Image.open(file_path)
    fmt = img.format

    if fmt not in SUPPORTED_FORMATS:
        return {
            "ok": False,
            "error_type": "unsupported_format",
            "detail": f"Format '{fmt}' is not supported. Supported: {SUPPORTED_FORMATS}",
        }

    width, height = img.size
    if width > MAX_RESOLUTION or height > MAX_RESOLUTION:
        return {
            "ok": False,
            "error_type": "image_too_large",
            "detail": f"Resolution {width}x{height} exceeds maximum {MAX_RESOLUTION}x{MAX_RESOLUTION}",
        }

    return {
        "ok": True,
        "format": fmt,
        "size_mb": round(size_mb, 1),
        "resolution": (width, height),
    }


def detect_skew_angle(binary_image: np.ndarray) -> float:
    coords = np.column_stack(np.where(binary_image < 128))

    if len(coords) < 100:
        return 0.0

    rect = cv2.minAreaRect(coords)
    angle = rect[-1]

    if angle < -45:
        angle = 90 + angle
    elif angle > 45:
        angle = angle - 90

    return angle


def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
    h, w = image.shape[:2]
    center = (w / 2, h / 2)

    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image, matrix, (w, h), borderMode=cv2.BORDER_REPLICATE
    )
    return rotated


def preprocess_for_ocr(image_path: str) -> dict:
    try:
        image = cv2.imread(image_path)
    except Exception as e:
        return {
            "ok": False,
            "error_type": "image_corrupted",
            "detail": str(e),
        }

    if image is None:
        return {
            "ok": False,
            "error_type": "image_corrupted",
            "detail": "Failed to read image file",
        }

    h, w = image.shape[:2]
    if h * w > MAX_PIXEL_COUNT:
        return {
            "ok": False,
            "error_type": "image_too_large",
            "detail": f"Pixel count {h * w} exceeds maximum {MAX_PIXEL_COUNT}",
        }

    steps_applied = []

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    steps_applied.append("grayscale")

    if h < 1000 or w < 1000:
        scale = 2.0
        gray = cv2.resize(
            gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC
        )
        steps_applied.append(f"upscale_x{scale:.1f}")

    denoised = cv2.medianBlur(gray, 3)
    steps_applied.append("denoise_median")

    binary = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=11,
        C=2,
    )
    steps_applied.append("adaptive_threshold")

    try:
        skew_angle = detect_skew_angle(binary)
        if abs(skew_angle) > 0.5:
            binary = rotate_image(binary, skew_angle)
            steps_applied.append(f"deskew_{skew_angle:.1f}")
    except Exception:
        pass

    pil_image = Image.fromarray(binary)

    return {
        "ok": True,
        "image": pil_image,
        "steps_applied": steps_applied,
    }
