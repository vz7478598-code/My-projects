import pytest
from analyzers.aggregator import aggregate_expenses, limit_categories


def test_basic_aggregation():
    transactions = [
        {"amount": 1000, "type": "expense", "category": "Продукты"},
        {"amount": 2000, "type": "expense", "category": "Продукты"},
        {"amount": 500, "type": "expense", "category": "Транспорт"},
    ]
    result = aggregate_expenses(transactions)
    assert result["categories"] == {"Продукты": 3000.0, "Транспорт": 500.0}
    assert result["total_expense"] == 3500.0


def test_income_excluded():
    transactions = [
        {"amount": 50000, "type": "income", "category": "Зарплата"},
        {"amount": 1000, "type": "expense", "category": "Продукты"},
    ]
    result = aggregate_expenses(transactions)
    assert "Зарплата" not in result["categories"]
    assert result["categories"] == {"Продукты": 1000.0}


def test_total_income():
    transactions = [
        {"amount": 85000, "type": "income", "category": "Другое"},
        {"amount": 1000, "type": "expense", "category": "Продукты"},
    ]
    result = aggregate_expenses(transactions)
    assert result["total_income"] == 85000.0
    assert result["total_expense"] == 1000.0


def test_empty():
    result = aggregate_expenses([])
    assert result["categories"] == {}
    assert result["total_expense"] == 0
    assert result["total_income"] == 0


def test_limit_categories():
    categories = {f"Cat{i}": float((10 - i) * 100) for i in range(10)}
    # Cat0=1000, Cat1=900, ..., Cat9=100
    result = limit_categories(categories, max_categories=4)
    assert len(result) == 4
    assert "Cat0" in result
    assert "Cat1" in result
    assert "Cat2" in result
    assert "Другое" in result
    expected_other = sum(float((10 - i) * 100) for i in range(3, 10))
    assert result["Другое"] == expected_other


def test_limit_not_needed():
    categories = {"A": 100.0, "B": 200.0, "C": 300.0}
    result = limit_categories(categories, max_categories=7)
    assert result == categories
