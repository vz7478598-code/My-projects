import os

import matplotlib.pyplot as plt
import pytest

from visualization.pie_chart import generate_pie_chart


def test_generate_basic(tmp_path):
    categories = {"Продукты": 15000, "Транспорт": 3000, "Кафе": 5000}
    output_path = str(tmp_path / "chart.png")
    result = generate_pie_chart(categories, output_path=output_path)
    assert result["ok"] is True
    assert result["path"] == output_path
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0


def test_generate_single_category(tmp_path):
    categories = {"Продукты": 15000}
    output_path = str(tmp_path / "single.png")
    result = generate_pie_chart(categories, output_path=output_path)
    assert result["ok"] is True
    assert os.path.exists(result["path"])


def test_empty_data():
    result = generate_pie_chart({})
    assert result["ok"] is False
    assert result["error_type"] == "no_data"


def test_custom_output_path(tmp_path):
    categories = {"Продукты": 15000, "Транспорт": 3000}
    custom_path = str(tmp_path / "custom_chart.png")
    result = generate_pie_chart(categories, output_path=custom_path)
    assert result["ok"] is True
    assert result["path"] == custom_path
    assert os.path.exists(custom_path)


def test_cleanup(tmp_path):
    categories = {"Продукты": 15000, "Транспорт": 3000}
    output_path = str(tmp_path / "cleanup.png")
    generate_pie_chart(categories, output_path=output_path)
    assert plt.get_fignums() == []
