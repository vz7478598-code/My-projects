"""Тесты для utils.number_parser."""

import pytest

from utils.number_parser import parse_amount


class TestParseAmount:
    def test_negative_with_spaces(self):
        assert parse_amount("-1 250,00") == -1250.0

    def test_positive_with_suffix(self):
        assert parse_amount("75 000,50 руб.") == 75000.5

    def test_positive_with_plus_sign(self):
        assert parse_amount("+85 000,00") == 85000.0

    def test_integer_amount(self):
        assert parse_amount("3 000,00") == 3000.0

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            parse_amount("")
