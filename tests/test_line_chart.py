"""Тесты для visualization/line_chart.py."""

import os
import tempfile

import matplotlib.pyplot as plt
import pytest

from visualization.line_chart import generate_line_chart


class TestGenerateLineChart:
    def test_generate_basic(self):
        records = [
            {"period_key": "2024-01", "total_expense": 35000, "total_income": 110000, "total_balance": 75000},
            {"period_key": "2024-02", "total_expense": 41000, "total_income": 120000, "total_balance": 85000},
            {"period_key": "2024-03", "total_expense": 45520, "total_income": 120000, "total_balance": 75000},
        ]
        output_path = os.path.join(tempfile.gettempdir(), "test_line_chart.png")
        result = generate_line_chart(records, output_path=output_path)

        assert result["ok"] is True
        assert os.path.exists(result["path"])
        assert os.path.getsize(result["path"]) > 0

        # Cleanup
        os.remove(result["path"])

    def test_not_enough_data(self):
        records = [
            {"period_key": "2024-01", "total_expense": 35000, "total_income": 110000, "total_balance": 75000},
        ]
        result = generate_line_chart(records)
        assert result["ok"] is False
        assert result["error_type"] == "not_enough_data"

    def test_not_enough_data_empty(self):
        result = generate_line_chart([])
        assert result["ok"] is False

    def test_cleanup(self):
        """После генерации графика все фигуры matplotlib должны быть закрыты."""
        records = [
            {"period_key": "2024-01", "total_expense": 35000, "total_income": 110000, "total_balance": 75000},
            {"period_key": "2024-02", "total_expense": 41000, "total_income": 120000, "total_balance": 85000},
        ]
        output_path = os.path.join(tempfile.gettempdir(), "test_line_chart_cleanup.png")
        generate_line_chart(records, output_path=output_path)

        assert plt.get_fignums() == []

        if os.path.exists(output_path):
            os.remove(output_path)

    def test_default_output_path(self):
        records = [
            {"period_key": "2024-01", "total_expense": 30000, "total_income": 100000, "total_balance": 70000},
            {"period_key": "2024-02", "total_expense": 40000, "total_income": 105000, "total_balance": 65000},
        ]
        result = generate_line_chart(records)
        assert result["ok"] is True
        assert "line_chart_" in result["path"]
        assert os.path.exists(result["path"])

        os.remove(result["path"])
