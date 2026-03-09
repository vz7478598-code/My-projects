"""Тесты для analyzers.balance_finder."""

import pytest

from analyzers.balance_finder import find_balance


def test_high_confidence():
    text = "Исходящий остаток: 75 000,50 руб."
    result = find_balance(text)
    assert result["ok"] is True
    assert result["amount"] == 75000.5
    assert result["confidence"] == "high"
    assert result["currency"] == "RUB"


def test_medium_confidence():
    text = "Доступный остаток 120 000,00 ₽"
    result = find_balance(text)
    assert result["ok"] is True
    assert result["amount"] == 120000.0
    assert result["confidence"] == "medium"


def test_low_confidence():
    text = "Остаток: 50 000,00"
    result = find_balance(text)
    assert result["ok"] is True
    assert result["amount"] == 50000.0
    assert result["confidence"] == "low"


def test_with_dollar():
    text = "Closing balance: 1 500.00 USD"
    result = find_balance(text)
    assert result["ok"] is True
    assert result["amount"] == 1500.0
    assert result["currency"] == "USD"
    assert result["confidence"] == "high"


def test_not_found():
    text = "Просто какой-то текст без баланса"
    result = find_balance(text)
    assert result["ok"] is False
    assert result["error_type"] == "balance_not_found"


def test_priority():
    text = (
        "Остаток: 10 000,00\n"
        "Исходящий остаток: 75 000,50 руб."
    )
    result = find_balance(text)
    assert result["ok"] is True
    assert result["amount"] == 75000.5
    assert result["confidence"] == "high"
