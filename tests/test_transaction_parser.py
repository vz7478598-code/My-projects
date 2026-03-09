from analyzers.transaction_parser import parse_transactions


def test_basic_expense():
    result = parse_transactions("01.03.2024 ПЯТЕРОЧКА -1 250,00")
    assert result["ok"] is True
    assert result["count"] == 1
    tx = result["transactions"][0]
    assert tx["amount"] == 1250.0
    assert tx["type"] == "expense"
    assert tx["date"] == "2024-03-01"


def test_basic_income():
    result = parse_transactions("03.03.2024 Пополнение Зарплата +85 000,00")
    assert result["ok"] is True
    tx = result["transactions"][0]
    assert tx["type"] == "income"
    assert tx["amount"] == 85000.0


def test_multiple():
    text = (
        "01.03.2024 ПЯТЕРОЧКА -1 250,00\n"
        "02.03.2024 ЯНДЕКС.ТАКСИ -350,00\n"
        "03.03.2024 Зарплата +85 000,00"
    )
    result = parse_transactions(text)
    assert result["ok"] is True
    assert result["count"] == 3


def test_no_sign_with_keyword():
    result = parse_transactions("01.03.2024 Покупка ПЯТЕРОЧКА 1 250,00")
    assert result["ok"] is True
    tx = result["transactions"][0]
    assert tx["type"] == "expense"


def test_empty():
    result = parse_transactions("Просто текст без транзакций")
    assert result["ok"] is False
    assert result["error_type"] == "no_transactions"


def test_full_statement():
    text = (
        "Выписка за период\n"
        "\n"
        "Дата Описание Сумма\n"
        "01.03.2024 ПЯТЕРОЧКА -1 250,00\n"
        "02.03.2024 ЯНДЕКС.ТАКСИ -350,00\n"
        "\n"
        "Исходящий остаток: 75 000,50"
    )
    result = parse_transactions(text)
    assert result["ok"] is True
    assert result["count"] == 2
