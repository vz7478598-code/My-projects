"""Тесты для parsers.ocr_postprocessor."""

import pytest

from parsers.ocr_postprocessor import clean_ocr_text


class TestRequiredCase:
    """Тест-кейс из задания."""

    def test_date_and_amount_combined(self):
        assert clean_ocr_text("О1.ОЗ.2024 -1 25О,ОО") == "01.03.2024 -1 250,00"


class TestDateFix:
    """Исправление кириллицы в датах."""

    def test_cyrillic_o_in_day(self):
        assert clean_ocr_text("О1.03.2024") == "01.03.2024"

    def test_cyrillic_o_in_month(self):
        assert clean_ocr_text("01.О3.2024") == "01.03.2024"

    def test_cyrillic_ze_in_month(self):
        assert clean_ocr_text("01.ОЗ.2024") == "01.03.2024"

    def test_all_cyrillic_in_date(self):
        assert clean_ocr_text("О1.ОЗ.2024") == "01.03.2024"

    def test_lowercase_o_in_day(self):
        assert clean_ocr_text("о1.03.2024") == "01.03.2024"

    def test_slash_separator(self):
        assert clean_ocr_text("О1/ОЗ/2024") == "01/03/2024"

    def test_hyphen_separator(self):
        assert clean_ocr_text("О1-ОЗ-2024") == "01-03-2024"

    def test_clean_date_unchanged(self):
        assert clean_ocr_text("01.03.2024") == "01.03.2024"

    def test_date_in_statement_line(self):
        result = clean_ocr_text("О1.ОЗ.2024 ПЯТЕРОЧКА -1 250,00")
        assert result == "01.03.2024 ПЯТЕРОЧКА -1 250,00"


class TestAmountFix:
    """Исправление кириллицы в суммах."""

    def test_cyrillic_o_in_kopeks(self):
        assert clean_ocr_text("250,ОО") == "250,00"

    def test_cyrillic_o_in_rubles(self):
        assert clean_ocr_text("25О,00") == "250,00"

    def test_negative_with_cyrillic(self):
        assert clean_ocr_text("-35О,ОО") == "-350,00"

    def test_with_thousands_space(self):
        assert clean_ocr_text("-1 25О,ОО") == "-1 250,00"

    def test_dot_decimal_separator(self):
        assert clean_ocr_text("25О.ОО") == "250.00"

    def test_clean_amount_unchanged(self):
        assert clean_ocr_text("1 250,00") == "1 250,00"


class TestCyrillicPreserved:
    """Кириллица в обычных словах НЕ затрагивается."""

    def test_operatsiya(self):
        assert clean_ocr_text("Операция по счёту") == "Операция по счёту"

    def test_opisanie(self):
        assert clean_ocr_text("Описание платежа") == "Описание платежа"

    def test_merchant_name(self):
        assert clean_ocr_text("ПЯТЕРОЧКА") == "ПЯТЕРОЧКА"

    def test_yandex_taxi_with_dot(self):
        assert clean_ocr_text("ЯНДЕКС.ТАКСИ") == "ЯНДЕКС.ТАКСИ"


class TestWhitespace:
    """Нормализация пробелов и пустых строк."""

    def test_multiple_spaces_collapsed(self):
        assert clean_ocr_text("дата  описание   сумма") == "дата описание сумма"

    def test_tabs_collapsed(self):
        assert clean_ocr_text("дата\t\tописание") == "дата описание"

    def test_newline_preserved(self):
        assert clean_ocr_text("строка1\nстрока2") == "строка1\nстрока2"

    def test_three_newlines_become_two(self):
        assert clean_ocr_text("а\n\n\nб") == "а\n\nб"

    def test_five_newlines_become_two(self):
        assert clean_ocr_text("а\n\n\n\n\nб") == "а\n\nб"

    def test_two_newlines_unchanged(self):
        assert clean_ocr_text("а\n\nб") == "а\n\nб"

    def test_leading_trailing_stripped(self):
        assert clean_ocr_text("  01.03.2024  ") == "01.03.2024"


class TestEdgeCases:
    """Граничные случаи."""

    def test_empty_string(self):
        assert clean_ocr_text("") == ""

    def test_full_statement_line(self):
        raw = "О1.ОЗ.2024  ПЯТЕРОЧКА   -1 25О,ОО"
        assert clean_ocr_text(raw) == "01.03.2024 ПЯТЕРОЧКА -1 250,00"

    def test_multiple_lines(self):
        raw = (
            "О1.ОЗ.2024  ПЯТЕРОЧКА   -1 25О,ОО\n"
            "О2.ОЗ.2024  ЯНДЕКС.ТАКСИ  -З5О,ОО"
        )
        expected = (
            "01.03.2024 ПЯТЕРОЧКА -1 250,00\n"
            "02.03.2024 ЯНДЕКС.ТАКСИ -350,00"
        )
        assert clean_ocr_text(raw) == expected
