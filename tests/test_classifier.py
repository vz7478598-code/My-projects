import pytest
from analyzers.classifier import classify_transactions


def _make_transaction(description, amount=-100.0, tx_type="debit"):
    return {
        "date": "01.01.2025",
        "description": description,
        "amount": amount,
        "type": tx_type,
        "raw_line": description,
    }


def test_products():
    txs = classify_transactions([_make_transaction("ПЯТЕРОЧКА")])
    assert txs[0]["category"] == "Продукты"


def test_transport():
    txs = classify_transactions([_make_transaction("ЯНДЕКС.ТАКСИ")])
    assert txs[0]["category"] == "Транспорт"


def test_cafe():
    txs = classify_transactions([_make_transaction("МАКДОНАЛДС")])
    assert txs[0]["category"] == "Кафе и рестораны"


def test_health():
    txs = classify_transactions([_make_transaction("АПТЕКА ОЗЕРКИ")])
    assert txs[0]["category"] == "Здоровье"


def test_transfer():
    txs = classify_transactions([_make_transaction("Перевод Иванову")])
    assert txs[0]["category"] == "Переводы"


def test_unknown():
    txs = classify_transactions([_make_transaction("КАКОЙ-ТО МАГАЗИН")])
    assert txs[0]["category"] == "Другое"


def test_multiple():
    txs = classify_transactions([
        _make_transaction("ПЯТЕРОЧКА"),
        _make_transaction("ЯНДЕКС.ТАКСИ"),
        _make_transaction("МАКДОНАЛДС"),
    ])
    assert txs[0]["category"] == "Продукты"
    assert txs[1]["category"] == "Транспорт"
    assert txs[2]["category"] == "Кафе и рестораны"


def test_case_insensitive():
    txs = classify_transactions([
        _make_transaction("пятерочка"),
        _make_transaction("ПЯТЕРОЧКА"),
    ])
    assert txs[0]["category"] == "Продукты"
    assert txs[1]["category"] == "Продукты"
