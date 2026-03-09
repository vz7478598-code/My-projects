"""Тесты для модуля предобработки изображений."""

import os
import sys
import tempfile

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from parsers.image_preprocessor import (
    detect_skew_angle,
    preprocess_for_ocr,
    rotate_image,
    validate_image,
)

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "test_samples")


def _create_test_image(fmt="PNG", size=(200, 100), color="white"):
    """Создаёт временное тестовое изображение."""
    img = Image.new("RGB", size, color)
    suffix = ".png" if fmt == "PNG" else ".jpg"
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    img.save(tmp.name, format=fmt)
    tmp.close()
    return tmp.name


# === validate_image ===


class TestValidateImage:
    def test_file_not_found(self):
        result = validate_image("nonexistent_file.png")
        assert result["ok"] is False
        assert result["error_type"] == "file_not_found"

    def test_valid_png(self):
        path = _create_test_image("PNG", (1920, 1080))
        try:
            result = validate_image(path)
            assert result["ok"] is True
            assert result["format"] == "PNG"
            assert result["resolution"] == (1920, 1080)
        finally:
            os.unlink(path)

    def test_valid_jpeg(self):
        path = _create_test_image("JPEG", (800, 600))
        try:
            result = validate_image(path)
            assert result["ok"] is True
            assert result["format"] == "JPEG"
            assert result["resolution"] == (800, 600)
        finally:
            os.unlink(path)

    def test_unsupported_format(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".bmp", delete=False)
        img = Image.new("RGB", (100, 100), "red")
        img.save(tmp.name, format="BMP")
        tmp.close()
        try:
            result = validate_image(tmp.name)
            assert result["ok"] is False
            assert result["error_type"] == "unsupported_format"
        finally:
            os.unlink(tmp.name)

    def test_corrupted_file(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.write(b"this is not an image")
        tmp.close()
        try:
            result = validate_image(tmp.name)
            assert result["ok"] is False
            assert result["error_type"] == "image_corrupted"
        finally:
            os.unlink(tmp.name)

    def test_resolution_too_large(self):
        path = _create_test_image("PNG", (8001, 100))
        try:
            result = validate_image(path)
            assert result["ok"] is False
            assert result["error_type"] == "image_too_large"
        finally:
            os.unlink(path)


# === preprocess_for_ocr ===


class TestPreprocessForOcr:
    def test_nonexistent_file(self):
        result = preprocess_for_ocr("nonexistent.png")
        assert result["ok"] is False

    def test_basic_pipeline(self):
        path = _create_test_image("PNG", (1200, 1000))
        try:
            result = preprocess_for_ocr(path)
            assert result["ok"] is True
            assert isinstance(result["image"], Image.Image)
            assert result["image"].mode == "L"
            assert "grayscale" in result["steps_applied"]
            assert "denoise_median" in result["steps_applied"]
            assert "adaptive_threshold" in result["steps_applied"]
        finally:
            os.unlink(path)

    def test_upscale_small_image(self):
        path = _create_test_image("PNG", (400, 300))
        try:
            result = preprocess_for_ocr(path)
            assert result["ok"] is True
            assert "upscale_x2.0" in result["steps_applied"]
        finally:
            os.unlink(path)

    def test_no_upscale_large_image(self):
        path = _create_test_image("PNG", (2000, 1500))
        try:
            result = preprocess_for_ocr(path)
            assert result["ok"] is True
            assert all("upscale" not in s for s in result["steps_applied"])
        finally:
            os.unlink(path)

    def test_output_is_binary(self):
        """Проверяет что выход содержит только чёрные и белые пиксели."""
        path = _create_test_image("PNG", (1200, 1000), color="gray")
        try:
            result = preprocess_for_ocr(path)
            assert result["ok"] is True
            arr = np.array(result["image"])
            unique_values = set(np.unique(arr))
            assert unique_values.issubset({0, 255})
        finally:
            os.unlink(path)


# === detect_skew_angle / rotate_image ===


class TestDeskew:
    def test_no_skew_on_blank(self):
        blank = np.ones((500, 500), dtype=np.uint8) * 255
        angle = detect_skew_angle(blank)
        assert angle == 0.0

    def test_rotate_preserves_shape(self):
        img = np.zeros((100, 200), dtype=np.uint8)
        rotated = rotate_image(img, 5.0)
        assert rotated.shape == img.shape


# === Интеграционный тест на скриншоте ===


class TestOnScreenshot:
    def test_screenshot_if_exists(self):
        """Если в test_samples/ есть скриншот — прогоняем полный конвейер."""
        if not os.path.isdir(SAMPLES_DIR):
            pytest.skip("Нет директории test_samples/")

        screenshots = [
            f
            for f in os.listdir(SAMPLES_DIR)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ]
        if not screenshots:
            pytest.skip("Нет скриншотов в test_samples/")

        path = os.path.join(SAMPLES_DIR, screenshots[0])
        result = preprocess_for_ocr(path)
        assert result["ok"] is True
        assert isinstance(result["image"], Image.Image)
        assert result["image"].mode == "L"

        # Сохраняем результат для визуальной проверки
        output_path = os.path.join(SAMPLES_DIR, "preprocessed_output.png")
        result["image"].save(output_path)
        print(f"\nРезультат сохранён: {output_path}")
        print(f"Шаги: {result['steps_applied']}")
        print(f"Размер: {result['image'].size}")
