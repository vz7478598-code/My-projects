"""
Модуль для работы с SQLite базой данных финансовой истории.

Зависимости: sqlite3, json (стандартная библиотека).
"""

import json
import os
import sqlite3
from datetime import datetime, timedelta


def init_db(db_path: str = "data/finance_history.db") -> sqlite3.Connection:
    """
    Инициализирует базу данных SQLite.

    Создаёт директорию если не существует, подключается к БД,
    настраивает WAL-режим, создаёт таблицу statements и индекс.

    Args:
        db_path: путь к файлу БД.

    Returns:
        sqlite3.Connection — подключение к БД.
    """
    dir_name = os.path.dirname(db_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA journal_mode=WAL")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS statements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period_key TEXT NOT NULL UNIQUE,
            analysis_date TEXT NOT NULL,
            file_name TEXT NOT NULL,
            total_balance REAL,
            total_income REAL DEFAULT 0,
            total_expense REAL DEFAULT 0,
            categories TEXT NOT NULL,
            is_reliable INTEGER DEFAULT 1
        )
    """)

    conn.execute("CREATE INDEX IF NOT EXISTS idx_period ON statements(period_key)")

    conn.commit()
    return conn


def save_statement(conn: sqlite3.Connection, data: dict) -> dict:
    """
    Сохраняет запись выписки в БД.

    Проверяет дубликат по period_key. Если запись уже существует —
    возвращает информацию о дубликате. Если новая — вставляет.

    Args:
        conn: подключение к БД.
        data: словарь с полями period_key, file_name, total_balance,
              total_income, total_expense, categories (dict), is_reliable (bool).

    Returns:
        dict с результатом операции.
    """
    try:
        cursor = conn.execute(
            "SELECT analysis_date FROM statements WHERE period_key = ?",
            (data["period_key"],),
        )
        existing = cursor.fetchone()

        if existing:
            return {
                "ok": True,
                "action": "duplicate",
                "existing_date": existing["analysis_date"],
            }

        conn.execute(
            """INSERT INTO statements
               (period_key, analysis_date, file_name, total_balance,
                total_income, total_expense, categories, is_reliable)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["period_key"],
                datetime.now().isoformat(),
                data["file_name"],
                data.get("total_balance"),
                data.get("total_income", 0),
                data.get("total_expense", 0),
                json.dumps(data.get("categories", {}), ensure_ascii=False),
                int(data.get("is_reliable", True)),
            ),
        )
        conn.commit()
        return {"ok": True, "action": "created"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def replace_statement(conn: sqlite3.Connection, data: dict) -> dict:
    """
    Заменяет существующую запись: DELETE по period_key, затем INSERT.

    Args:
        conn: подключение к БД.
        data: словарь с полями (аналогично save_statement).

    Returns:
        dict с результатом операции.
    """
    try:
        conn.execute(
            "DELETE FROM statements WHERE period_key = ?",
            (data["period_key"],),
        )
        conn.execute(
            """INSERT INTO statements
               (period_key, analysis_date, file_name, total_balance,
                total_income, total_expense, categories, is_reliable)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["period_key"],
                datetime.now().isoformat(),
                data["file_name"],
                data.get("total_balance"),
                data.get("total_income", 0),
                data.get("total_expense", 0),
                json.dumps(data.get("categories", {}), ensure_ascii=False),
                int(data.get("is_reliable", True)),
            ),
        )
        conn.commit()
        return {"ok": True, "action": "replaced"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_history(conn: sqlite3.Connection, months: int = 12) -> dict:
    """
    Получает историю выписок за последние N месяцев.

    Вычисляет cutoff в формате YYYY-MM для N месяцев назад
    и выбирает записи с period_key >= cutoff.

    Args:
        conn: подключение к БД.
        months: количество месяцев назад (по умолчанию 12).

    Returns:
        dict со списком записей.
    """
    try:
        now = datetime.now()
        # Вычисляем дату N месяцев назад
        year = now.year
        month = now.month - months
        while month <= 0:
            month += 12
            year -= 1
        cutoff = f"{year:04d}-{month:02d}"

        cursor = conn.execute(
            "SELECT * FROM statements WHERE period_key >= ? ORDER BY period_key ASC",
            (cutoff,),
        )
        rows = cursor.fetchall()

        records = []
        for row in rows:
            records.append({
                "period_key": row["period_key"],
                "total_balance": row["total_balance"],
                "total_income": row["total_income"],
                "total_expense": row["total_expense"],
                "categories": json.loads(row["categories"]),
                "is_reliable": bool(row["is_reliable"]),
                "file_name": row["file_name"],
            })

        return {"ok": True, "count": len(records), "records": records}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def check_db_integrity(db_path: str) -> dict:
    """
    Проверяет целостность базы данных.

    Выполняет PRAGMA integrity_check. Если БД повреждена —
    переименовывает в .backup и пересоздаёт через init_db.

    Args:
        db_path: путь к файлу БД.

    Returns:
        dict с результатом проверки.
    """
    try:
        conn = sqlite3.connect(db_path)
        result = conn.execute("PRAGMA integrity_check").fetchone()
        conn.close()

        if result[0] == "ok":
            return {"ok": True}

        # БД повреждена — переименовываем и пересоздаём
        backup_path = db_path + ".backup"
        os.rename(db_path, backup_path)
        init_db(db_path)
        return {"ok": False, "recovered": True, "backup_path": backup_path}
    except Exception as e:
        # Если даже подключиться не удалось — тоже восстанавливаем
        backup_path = db_path + ".backup"
        try:
            if os.path.exists(db_path):
                os.rename(db_path, backup_path)
            init_db(db_path)
            return {"ok": False, "recovered": True, "backup_path": backup_path}
        except Exception as inner_e:
            return {"ok": False, "error": str(inner_e)}
