"""Поиск баланса в тексте банковской выписки."""

import re

from utils.number_parser import parse_amount

_KEYWORDS_BY_PRIORITY = [
    (
        "high",
        [
            "исходящий остаток",
            "остаток на конец периода",
            "closing balance",
        ],
    ),
    (
        "medium",
        [
            "баланс",
            "остаток по счёту",
            "итого на счёте",
            "доступный остаток",
        ],
    ),
    (
        "low",
        [
            "остаток",
            "balance",
            "итого",
        ],
    ),
]

_CURRENCY_MAP = {
    "руб": "RUB",
    "руб.": "RUB",
    "₽": "RUB",
    "rub": "RUB",
    "$": "USD",
    "usd": "USD",
    "€": "EUR",
    "eur": "EUR",
}

_DEFAULT_CURRENCY = "RUB"


def _detect_currency(raw: str | None) -> str:
    if not raw:
        return _DEFAULT_CURRENCY
    return _CURRENCY_MAP.get(raw.lower().rstrip("."), _DEFAULT_CURRENCY)


def _parse_matched_amount(raw: str) -> float:
    """Парсит сумму из regex-совпадения.

    Обрабатывает оба формата десятичного разделителя:
    - "75 000,50" (запятая) — передаём в parse_amount
    - "1 500.00" (точка) — заменяем точку на запятую для parse_amount
    """
    stripped = raw.strip()
    if "," in stripped:
        return parse_amount(stripped)
    if "." in stripped:
        return parse_amount(stripped.replace(".", ","))
    return parse_amount(stripped)


def find_balance(text: str) -> dict:
    """Ищет баланс в тексте банковской выписки.

    Возвращает словарь с результатом поиска.
    """
    for confidence, keywords in _KEYWORDS_BY_PRIORITY:
        for keyword in keywords:
            pattern = (
                r"(?:"
                + re.escape(keyword)
                + r")[:\s]*([−\-+]?[\d\s]+[.,]\d{2})"
                + r"\s*(руб\.?|₽|\$|€|RUB|USD|EUR)?"
            )
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                raw_amount = match.group(1)
                raw_currency = match.group(2)
                amount = _parse_matched_amount(raw_amount)
                currency = _detect_currency(raw_currency)
                return {
                    "ok": True,
                    "amount": amount,
                    "currency": currency,
                    "confidence": confidence,
                    "raw_match": match.group(0).strip(),
                }

    return {
        "ok": False,
        "error_type": "balance_not_found",
        "detail": "Не удалось найти баланс в тексте",
    }
