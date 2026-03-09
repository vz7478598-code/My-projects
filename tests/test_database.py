"""
Тесты для storage.database.

Все тесты используют tmp_path для создания временной БД.
Хелпер _month_key() генерирует period_key относительно текущей даты,
чтобы записи всегда попадали в окно get_history.
"""

import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from storage.database import (
    check_db_integrity,
    get_history,
    init_db,
    replace_statement,
    save_statement,
)


def _month_key(months_ago: int = 0) -> str:
    """Возвращает period_key вида YYYY-MM для N месяцев назад от текущей даты."""
    dt = datetime.now() - timedelta(days=months_ago * 30)
    return dt.strftime("%Y-%m")


def test_init_db(tmp_path):
    """Создать БД в tmp_path → conn не None, таблица существует."""
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    assert conn is not None

    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='statements'"
    )
    assert cursor.fetchone() is not None
    conn.close()


def test_save_and_get(tmp_path):
    """
    Сохранить запись → action='created'.
    get_history → count=1, period_key совпадает, categories десериализуются.
    """
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)

    pk = _month_key(2)
    data = {
        "period_key": pk,
        "file_name": "statement_march.pdf",
        "total_balance": 90000,
        "total_income": 50000,
        "total_expense": 30000,
        "categories": {"Еда": 15000, "Транспорт": 5000},
        "is_reliable": True,
    }
    result = save_statement(conn, data)
    assert result["ok"] is True
    assert result["action"] == "created"

    history = get_history(conn, months=12)
    assert history["ok"] is True
    assert history["count"] == 1
    assert history["records"][0]["period_key"] == pk
    assert history["records"][0]["categories"] == {"Еда": 15000, "Транспорт": 5000}
    conn.close()


def test_duplicate(tmp_path):
    """Сохранить одну и ту же period_key дважды → второй раз action='duplicate'."""
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)

    pk = _month_key(1)
    data = {
        "period_key": pk,
        "file_name": "statement.pdf",
        "total_balance": 90000,
        "categories": {},
    }
    save_statement(conn, data)

    result = save_statement(conn, data)
    assert result["ok"] is True
    assert result["action"] == "duplicate"
    assert "existing_date" in result
    conn.close()


def test_replace(tmp_path):
    """
    Сохранить запись, затем replace с новым total_balance.
    get_history → count=1, новый total_balance.
    """
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)

    pk = _month_key(1)
    data = {
        "period_key": pk,
        "file_name": "statement.pdf",
        "total_balance": 90000,
        "categories": {},
    }
    save_statement(conn, data)

    data["total_balance"] = 120000
    result = replace_statement(conn, data)
    assert result["ok"] is True
    assert result["action"] == "replaced"

    history = get_history(conn, months=12)
    assert history["count"] == 1
    assert history["records"][0]["total_balance"] == 120000
    conn.close()


def test_history_filter(tmp_path):
    """
    Сохранить записи за 24, 3 и 1 месяц назад.
    get_history(months=6) → не возвращает запись за 24 месяца.
    """
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)

    old_key = _month_key(24)
    mid_key = _month_key(3)
    new_key = _month_key(1)

    for pk in [old_key, mid_key, new_key]:
        save_statement(conn, {
            "period_key": pk,
            "file_name": f"stmt_{pk}.pdf",
            "total_balance": 10000,
            "categories": {},
        })

    history = get_history(conn, months=6)
    keys = [r["period_key"] for r in history["records"]]
    assert old_key not in keys
    conn.close()


def test_integrity_ok(tmp_path):
    """Проверить валидную БД → {'ok': True}."""
    db_path = str(tmp_path / "test.db")
    init_db(db_path)

    result = check_db_integrity(db_path)
    assert result["ok"] is True
