# 04. SQLite — Локальное хранилище истории

## Назначение в проекте

Встраиваемая база данных для хранения результатов анализа выписок между сеансами работы приложения. Используется на **Этапе 4**. Хранит: период, баланс, суммы расходов по категориям. Позволяет строить тренды и сравнивать месяцы.

## Установка

```bash
# Входит в стандартную библиотеку Python — установка не требуется
import sqlite3  # уже есть
```

**Файл БД:** `data/finance_history.db` (создаётся автоматически при первом запуске)

## Схема базы данных

```sql
-- schema.sql

CREATE TABLE IF NOT EXISTS statements (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    period_key      TEXT NOT NULL UNIQUE,           -- "2024-03" (YYYY-MM)
    analysis_date   TEXT NOT NULL,                   -- ISO 8601: "2024-04-05T14:30:00"
    file_name       TEXT NOT NULL,                   -- "выписка_март.pdf"
    total_balance   REAL,                            -- 75000.50
    total_income    REAL DEFAULT 0,                  -- 120000.00
    total_expense   REAL DEFAULT 0,                  -- 45520.50
    categories      TEXT NOT NULL,                   -- JSON: {"Продукты": 15000, ...}
    is_reliable     INTEGER DEFAULT 1               -- 1=период определён точно, 0=по дате загрузки
);

CREATE INDEX IF NOT EXISTS idx_period ON statements(period_key);
```

## API: Все операции с хранилищем

### Инициализация

```python
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join("data", "finance_history.db")

def init_db() -> sqlite3.Connection:
    """
    Создаёт БД и таблицу, если не существуют.
    Возвращает соединение.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # доступ по имени столбца
    conn.execute("PRAGMA journal_mode=WAL")  # безопаснее при сбоях
    conn.execute("""
        CREATE TABLE IF NOT EXISTS statements (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            period_key      TEXT NOT NULL UNIQUE,
            analysis_date   TEXT NOT NULL,
            file_name       TEXT NOT NULL,
            total_balance   REAL,
            total_income    REAL DEFAULT 0,
            total_expense   REAL DEFAULT 0,
            categories      TEXT NOT NULL,
            is_reliable     INTEGER DEFAULT 1
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_period ON statements(period_key)")
    conn.commit()
    return conn
```

```python
>>> conn = init_db()
# Создаёт файл data/finance_history.db если не существует
```

### Сохранение записи

**Вход:** данные анализа выписки
**Выход:** успех/ошибка + флаг дубликата

```python
def save_statement(conn: sqlite3.Connection, data: dict) -> dict:
    """
    Сохраняет результат анализа выписки.

    Вход (data):
    {
        "period_key": "2024-03",
        "file_name": "выписка_март.pdf",
        "total_balance": 75000.50,
        "total_income": 120000.00,
        "total_expense": 45520.50,
        "categories": {"Продукты": 15420.50, "Транспорт": 3050.00, ...},
        "is_reliable": True
    }

    Возвращает:
    {"ok": True, "action": "created"}
    {"ok": True, "action": "duplicate", "existing_date": "2024-04-01T10:00:00"}
    {"ok": False, "error": "..."}
    """
    try:
        # Проверка на дубликат
        existing = conn.execute(
            "SELECT analysis_date FROM statements WHERE period_key = ?",
            (data["period_key"],)
        ).fetchone()

        if existing:
            return {
                "ok": True,
                "action": "duplicate",
                "existing_date": existing["analysis_date"]
            }

        # Вставка новой записи
        conn.execute("""
            INSERT INTO statements
            (period_key, analysis_date, file_name, total_balance,
             total_income, total_expense, categories, is_reliable)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["period_key"],
            datetime.now().isoformat(),
            data["file_name"],
            data.get("total_balance"),
            data.get("total_income", 0),
            data.get("total_expense", 0),
            json.dumps(data["categories"], ensure_ascii=False),
            1 if data.get("is_reliable", True) else 0
        ))
        conn.commit()
        return {"ok": True, "action": "created"}

    except sqlite3.OperationalError as e:
        return {"ok": False, "error": f"Ошибка БД: {e}"}
```

**Примеры:**
```python
>>> save_statement(conn, {
...     "period_key": "2024-03",
...     "file_name": "выписка_март.pdf",
...     "total_balance": 75000.50,
...     "total_income": 120000.00,
...     "total_expense": 45520.50,
...     "categories": {"Продукты": 15420.50, "Транспорт": 3050.00, "Другое": 1150.00},
...     "is_reliable": True
... })
{"ok": True, "action": "created"}

>>> # Повторная загрузка за тот же месяц:
>>> save_statement(conn, {"period_key": "2024-03", ...})
{"ok": True, "action": "duplicate", "existing_date": "2024-04-05T14:30:00"}
```

### Замена существующей записи (после подтверждения пользователем)

```python
def replace_statement(conn: sqlite3.Connection, data: dict) -> dict:
    """
    Заменяет запись за тот же период.
    Вызывается, когда пользователь нажал "Да" в диалоге подтверждения.
    """
    try:
        conn.execute("DELETE FROM statements WHERE period_key = ?",
                     (data["period_key"],))
        conn.execute("""
            INSERT INTO statements
            (period_key, analysis_date, file_name, total_balance,
             total_income, total_expense, categories, is_reliable)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["period_key"],
            datetime.now().isoformat(),
            data["file_name"],
            data.get("total_balance"),
            data.get("total_income", 0),
            data.get("total_expense", 0),
            json.dumps(data["categories"], ensure_ascii=False),
            1 if data.get("is_reliable", True) else 0
        ))
        conn.commit()
        return {"ok": True, "action": "replaced"}
    except sqlite3.OperationalError as e:
        return {"ok": False, "error": str(e)}
```

### Получение истории за N месяцев

**Вход:** количество месяцев (int, по умолчанию 12)
**Выход:** список записей, отсортированных по period_key

```python
def get_history(conn: sqlite3.Connection, months: int = 12) -> dict:
    """
    Возвращает:
    {
        "ok": True,
        "count": 5,
        "records": [
            {
                "period_key": "2023-11",
                "total_balance": 80000.00,
                "total_expense": 42000.00,
                "categories": {"Продукты": 14000, ...}
            },
            ...  (отсортировано по period_key ASC)
        ]
    }
    """
    try:
        # Вычисляем дату N месяцев назад в формате YYYY-MM
        now = datetime.now()
        year = now.year
        month = now.month - months
        while month <= 0:
            month += 12
            year -= 1
        cutoff = f"{year:04d}-{month:02d}"

        rows = conn.execute("""
            SELECT period_key, analysis_date, file_name,
                   total_balance, total_income, total_expense,
                   categories, is_reliable
            FROM statements
            WHERE period_key >= ?
            ORDER BY period_key ASC
        """, (cutoff,)).fetchall()

        records = []
        for row in rows:
            records.append({
                "period_key": row["period_key"],
                "total_balance": row["total_balance"],
                "total_income": row["total_income"],
                "total_expense": row["total_expense"],
                "categories": json.loads(row["categories"]),
                "is_reliable": bool(row["is_reliable"]),
                "file_name": row["file_name"]
            })

        return {"ok": True, "count": len(records), "records": records}

    except sqlite3.OperationalError as e:
        return {"ok": False, "error": str(e), "records": []}
```

**Пример результата:**
```python
>>> history = get_history(conn, months=12)
>>> history["count"]
3
>>> history["records"]
[
    {
        "period_key": "2024-01",
        "total_balance": 90000.00,
        "total_expense": 38000.00,
        "categories": {"Продукты": 12000, "Транспорт": 4000, "Кафе и рестораны": 6000, "Другое": 16000},
        "is_reliable": True,
        "file_name": "jan_2024.pdf"
    },
    {
        "period_key": "2024-02",
        "total_balance": 85000.00,
        "total_expense": 41000.00,
        "categories": {"Продукты": 14000, "Транспорт": 3500, "Кафе и рестораны": 7500, "Другое": 16000},
        "is_reliable": True,
        "file_name": "feb_2024.pdf"
    },
    {
        "period_key": "2024-03",
        "total_balance": 75000.50,
        "total_expense": 45520.50,
        "categories": {"Продукты": 15420.50, "Транспорт": 3050, "Кафе и рестораны": 5200, "Другое": 21850.50},
        "is_reliable": True,
        "file_name": "выписка_март.pdf"
    }
]
```

### Проверка целостности БД

```python
def check_db_integrity(db_path: str) -> dict:
    """
    Проверяет файл БД. Если повреждён — создаёт бэкап и новую пустую БД.

    Возвращает:
    {"ok": True}
    {"ok": False, "recovered": True, "backup_path": "..."}
    {"ok": False, "recovered": False, "error": "..."}
    """
    try:
        conn = sqlite3.connect(db_path)
        result = conn.execute("PRAGMA integrity_check").fetchone()
        conn.close()

        if result[0] == "ok":
            return {"ok": True}
        else:
            # БД повреждена — бэкап и пересоздание
            backup_path = db_path + ".backup"
            os.rename(db_path, backup_path)
            init_db()  # создаст новую пустую БД
            return {"ok": False, "recovered": True, "backup_path": backup_path}

    except Exception as e:
        # Файл сильно повреждён
        try:
            backup_path = db_path + ".backup"
            if os.path.exists(db_path):
                os.rename(db_path, backup_path)
            init_db()
            return {"ok": False, "recovered": True, "backup_path": backup_path}
        except Exception as e2:
            return {"ok": False, "recovered": False, "error": str(e2)}
```

## SQL-запросы (справочник)

```sql
-- Все записи за последний год
SELECT * FROM statements
WHERE period_key >= '2023-04'
ORDER BY period_key ASC;

-- Проверить дубликат
SELECT COUNT(*) FROM statements WHERE period_key = '2024-03';

-- Удалить запись за период
DELETE FROM statements WHERE period_key = '2024-03';

-- Суммарные расходы за все периоды
SELECT SUM(total_expense) as total FROM statements;

-- Последняя загруженная выписка
SELECT * FROM statements ORDER BY analysis_date DESC LIMIT 1;
```

## Конфигурация

```python
# config.py (значения, которые должны быть конфигурируемыми)

HISTORY_MONTHS = 12          # сколько месяцев отображать на графике
MAX_CHART_CATEGORIES = 7     # лимит категорий на графике (остальные → «Другое»)
ANOMALY_THRESHOLD = 500      # %: изменение > 500% считается аномалией
DB_PATH = "data/finance_history.db"
```

## Ограничения

- Файл БД хранится локально → при удалении теряется вся история
- Однопользовательский режим (одно приложение = один файл)
- Нет шифрования данных (финансовые данные хранятся в открытом виде)
- `categories` хранится как JSON-строка → нельзя делать SQL-запросы по отдельным категориям
