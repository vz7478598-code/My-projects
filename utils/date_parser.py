"""Парсинг дат и периодов из банковских выписок."""

import re
import datetime

MONTHS_RU = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
    "мая": 5, "июня": 6, "июля": 7, "августа": 8,
    "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
    "январь": 1, "февраль": 2, "март": 3, "апрель": 4,
    "май": 5, "июнь": 6, "июль": 7, "август": 8,
    "сентябрь": 9, "октябрь": 10, "ноябрь": 11, "декабрь": 12,
}

_RE_DOT = re.compile(r"^(\d{1,2})\.(\d{2})\.(\d{4})$")
_RE_SLASH = re.compile(r"^(\d{1,2})/(\d{2})/(\d{4})$")
_RE_RU = re.compile(
    r"^(\d{1,2})\s+(" + "|".join(MONTHS_RU) + r")\s+(\d{4})$",
    re.IGNORECASE,
)
_RE_PERIOD = re.compile(
    r"за\s+период\s+с\s+(\d{1,2}[./]\d{2}[./]\d{4})\s+по\s+(\d{1,2}[./]\d{2}[./]\d{4})",
    re.IGNORECASE,
)


def parse_date(text: str) -> str:
    """Парсит дату из строки и возвращает формат YYYY-MM-DD.

    Поддерживаемые форматы:
        DD.MM.YYYY  (01.03.2024)
        DD/MM/YYYY  (01/03/2024)
        D месяц YYYY (1 марта 2024)

    Raises:
        ValueError: если формат не распознан или дата невалидна.
    """
    s = text.strip()

    m = _RE_DOT.match(s)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return _validate_and_format(year, month, day)

    m = _RE_SLASH.match(s)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return _validate_and_format(year, month, day)

    m = _RE_RU.match(s)
    if m:
        day = int(m.group(1))
        month = MONTHS_RU[m.group(2).lower()]
        year = int(m.group(3))
        return _validate_and_format(year, month, day)

    raise ValueError(f"Неизвестный формат даты: {text!r}")


def extract_period(text: str) -> str | None:
    """Извлекает период из текста выписки.

    Ищет паттерн «за период с DD.MM.YYYY по DD.MM.YYYY»
    и возвращает YYYY-MM начальной даты.

    Returns:
        Строка YYYY-MM или None, если паттерн не найден.
    """
    m = _RE_PERIOD.search(text)
    if not m:
        return None
    start_raw = m.group(1).replace("/", ".")
    date_str = parse_date(start_raw)
    return date_str[:7]  # YYYY-MM


def _validate_and_format(year: int, month: int, day: int) -> str:
    """Валидирует дату и возвращает строку YYYY-MM-DD."""
    d = datetime.date(year, month, day)
    return d.isoformat()
