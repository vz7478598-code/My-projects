"""Тесты для analyzers/trend_analyzer.py."""

import pytest

from analyzers.trend_analyzer import analyze_trends, generate_trend_comment


class TestAnalyzeTrends:
    def test_basic_trend(self):
        records = [
            {
                "period_key": "2024-02",
                "total_expense": 41000,
                "total_income": 120000,
                "total_balance": 85000,
                "categories": {"Продукты": 14000, "Транспорт": 3500},
            },
            {
                "period_key": "2024-03",
                "total_expense": 45520,
                "total_income": 120000,
                "total_balance": 75000,
                "categories": {"Продукты": 15420, "Транспорт": 3050},
            },
        ]
        result = analyze_trends(records)
        assert result["ok"] is True
        assert result["current_period"] == "2024-03"
        assert result["previous_period"] == "2024-02"
        assert result["expense_change"] == 4520
        assert result["balance_change"] == -10000

    def test_category_changes(self):
        records = [
            {
                "period_key": "2024-02",
                "total_expense": 41000,
                "total_income": 120000,
                "total_balance": 85000,
                "categories": {"Продукты": 14000, "Транспорт": 3500},
            },
            {
                "period_key": "2024-03",
                "total_expense": 45520,
                "total_income": 120000,
                "total_balance": 75000,
                "categories": {"Продукты": 15420, "Транспорт": 3050},
            },
        ]
        result = analyze_trends(records)
        changes = {c["category"]: c for c in result["category_changes"]}

        assert "Продукты" in changes
        assert changes["Продукты"]["change"] == 1420

        assert "Транспорт" in changes
        assert changes["Транспорт"]["change"] == -450

    def test_not_enough_data(self):
        result = analyze_trends([
            {
                "period_key": "2024-01",
                "total_expense": 30000,
                "total_income": 100000,
                "total_balance": 70000,
                "categories": {},
            }
        ])
        assert result["ok"] is False
        assert result["error_type"] == "not_enough_data"

    def test_not_enough_data_empty(self):
        result = analyze_trends([])
        assert result["ok"] is False
        assert result["error_type"] == "not_enough_data"

    def test_anomaly(self):
        records = [
            {
                "period_key": "2024-02",
                "total_expense": 10000,
                "total_income": 100000,
                "total_balance": 90000,
                "categories": {"Редкая категория": 100},
            },
            {
                "period_key": "2024-03",
                "total_expense": 20000,
                "total_income": 100000,
                "total_balance": 80000,
                "categories": {"Редкая категория": 10000},
            },
        ]
        result = analyze_trends(records)
        assert result["ok"] is True

        anomaly_cats = [a["category"] for a in result["anomalies"]]
        assert "Редкая категория" in anomaly_cats

        anomaly = next(a for a in result["anomalies"] if a["category"] == "Редкая категория")
        assert abs(anomaly["change_pct"]) > 500


class TestGenerateTrendComment:
    def test_comment_generation(self):
        records = [
            {
                "period_key": "2024-02",
                "total_expense": 41000,
                "total_income": 120000,
                "total_balance": 85000,
                "categories": {"Продукты": 14000, "Транспорт": 3500},
            },
            {
                "period_key": "2024-03",
                "total_expense": 45520,
                "total_income": 120000,
                "total_balance": 75000,
                "categories": {"Продукты": 15420, "Транспорт": 3050},
            },
        ]
        trend_data = analyze_trends(records)
        comment = generate_trend_comment(trend_data)

        assert isinstance(comment, str)
        assert len(comment) > 0
        assert "выросли" in comment or "снизились" in comment
        assert "2024-03" in comment

    def test_comment_with_anomaly(self):
        records = [
            {
                "period_key": "2024-02",
                "total_expense": 10000,
                "total_income": 100000,
                "total_balance": 90000,
                "categories": {"Редкая": 100},
            },
            {
                "period_key": "2024-03",
                "total_expense": 20000,
                "total_income": 100000,
                "total_balance": 80000,
                "categories": {"Редкая": 10000},
            },
        ]
        trend_data = analyze_trends(records)
        comment = generate_trend_comment(trend_data)
        assert "Аномальное изменение" in comment

    def test_comment_not_enough_data(self):
        trend_data = analyze_trends([])
        comment = generate_trend_comment(trend_data)
        assert "Нужно минимум" in comment or "Недостаточно" in comment
