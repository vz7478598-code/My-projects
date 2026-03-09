import os
import tempfile

import numpy as np
import pytest
from PIL import Image, ImageDraw

from parsers.image_preprocessor import preprocess_for_ocr, validate_image


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


def test_validate_png(tmp_dir):
    path = os.path.join(tmp_dir, "test.png")
    img = Image.new("RGB", (100, 100), color="white")
    img.save(path, format="PNG")

    result = validate_image(path)
    assert result["ok"] is True
    assert result["format"] == "PNG"
    assert result["resolution"] == (100, 100)
    assert result["size_mb"] >= 0


def test_validate_unsupported(tmp_dir):
    path = os.path.join(tmp_dir, "test.bmp")
    img = Image.new("RGB", (100, 100), color="white")
    img.save(path, format="BMP")

    result = validate_image(path)
    assert result["ok"] is False
    assert result["error_type"] == "unsupported_format"


def test_validate_too_large(tmp_dir):
    path = os.path.join(tmp_dir, "large.png")
    with open(path, "wb") as f:
        f.write(b"\x00" * (11 * 1024 * 1024))

    result = validate_image(path)
    assert result["ok"] is False
    assert result["error_type"] == "image_too_large"


def test_preprocess_small_image(tmp_dir):
    path = os.path.join(tmp_dir, "small.png")
    img = Image.new("RGB", (500, 500), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((100, 200), "Hello World", fill="black")
    img.save(path, format="PNG")

    result = preprocess_for_ocr(path)
    assert result["ok"] is True
    assert "upscale_x2.0" in result["steps_applied"]
    assert "grayscale" in result["steps_applied"]
    assert isinstance(result["image"], Image.Image)


def test_preprocess_normal_image(tmp_dir):
    path = os.path.join(tmp_dir, "normal.png")
    img = Image.new("RGB", (1500, 1500), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((300, 600), "Normal size text", fill="black")
    img.save(path, format="PNG")

    result = preprocess_for_ocr(path)
    assert result["ok"] is True
    assert all("upscale" not in s for s in result["steps_applied"])
    assert "grayscale" in result["steps_applied"]


def test_preprocess_corrupted(tmp_dir):
    path = os.path.join(tmp_dir, "corrupted.png")
    with open(path, "wb") as f:
        f.write(b"not an image at all")

    result = preprocess_for_ocr(path)
    assert result["ok"] is False
    assert result["error_type"] == "image_corrupted"
