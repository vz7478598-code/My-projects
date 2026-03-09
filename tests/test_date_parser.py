"""Тесты для utils.date_parser."""

import pytest

from utils.date_parser import extract_period, parse_date


class TestParseDate:
    def test_dot_format(self):
        assert parse_date("01.03.2024") == "2024-03-01"

    def test_dot_format_single_digit_day(self):
        assert parse_date("5.11.2023") == "2023-11-05"

    def test_slash_format(self):
        assert parse_date("01/03/2024") == "2024-03-01"

    def test_slash_format_single_digit_day(self):
        assert parse_date("9/01/2025") == "2025-01-09"

    def test_russian_month_genitive(self):
        assert parse_date("1 марта 2024") == "2024-03-01"

    def test_russian_month_january(self):
        assert parse_date("15 января 2025") == "2025-01-15"

    def test_russian_month_nominative(self):
        assert parse_date("20 декабрь 2023") == "2023-12-20"

    def test_russian_month_case_insensitive(self):
        assert parse_date("7 Июня 2024") == "2024-06-07"

    def test_whitespace_trimmed(self):
        assert parse_date("  01.03.2024  ") == "2024-03-01"

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            parse_date("abc")

    def test_invalid_date_raises(self):
        with pytest.raises(ValueError):
            parse_date("31.02.2024")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            parse_date("")


class TestExtractPeriod:
    def test_basic_period(self):
        text = "За период с 01.03.2024 по 31.03.2024"
        assert extract_period(text) == "2024-03"

    def test_period_in_multiline_text(self):
        text = (
            "Выписка по счёту 40817810000000000001\n"
            "За период с 01.03.2024 по 31.03.2024\n"
            "\nДата       Описание              Сумма\n"
        )
        assert extract_period(text) == "2024-03"

    def test_period_lowercase(self):
        text = "за период с 15.01.2025 по 15.02.2025"
        assert extract_period(text) == "2025-01"

    def test_period_with_slashes(self):
        text = "За период с 01/06/2024 по 30/06/2024"
        assert extract_period(text) == "2024-06"

    def test_no_period_returns_none(self):
        assert extract_period("текст без периода") is None

    def test_empty_string_returns_none(self):
        assert extract_period("") is None
