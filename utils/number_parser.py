"""Парсинг денежных сумм из русскоязычных банковских выписок."""

import re


_RE_CLEANUP = re.compile(r"[^\d,\-+]")


def parse_amount(raw: str) -> float:
    """Парсит денежную сумму из строки и возвращает float.

    Поддерживаемые форматы:
        - "-1 250,00"   → -1250.0
        - "75 000,50 руб." → 75000.5
        - "+85 000,00"  → 85000.0

    Пробелы считаются разделителями тысяч, запятая — десятичным разделителем.

    Raises:
        ValueError: если строка не содержит распознаваемого числа.
    """
    if not raw or not raw.strip():
        raise ValueError(f"Пустая строка: {raw!r}")

    cleaned = _RE_CLEANUP.sub("", raw)

    if not cleaned:
        raise ValueError(f"Не удалось распознать сумму: {raw!r}")

    cleaned = cleaned.replace(",", ".")

    try:
        return float(cleaned)
    except ValueError:
        raise ValueError(f"Не удалось распознать сумму: {raw!r}")
