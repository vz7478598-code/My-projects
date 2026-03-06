# 01. pdfplumber — Извлечение текста из PDF

## Назначение в проекте

Основная библиотека для чтения текста из PDF-выписок банков. Используется на **Этапах 2–4**. Извлекает текст с сохранением структуры (строки, колонки), что критично для парсинга банковских таблиц.

## Установка

```bash
pip install pdfplumber==0.11.4
pip install PyPDF2==3.0.1   # для проверки пароля/целостности
```

## Почему именно pdfplumber

- Лучше всего работает с табличными данными в PDF (банковские выписки)
- Сохраняет позиционирование текста (колонки не «слипаются»)
- Хорошо работает с кириллицей
- PyMuPDF быстрее, но хуже обрабатывает таблицы; tabula-py требует Java

## API: Основные операции

### 1. Проверка целостности и пароля (PyPDF2)

**Вход:** путь к файлу (str)
**Выход:** True/False + тип ошибки

```python
import PyPDF2

def check_pdf_integrity(file_path: str) -> dict:
    """
    Возвращает:
    {"ok": True} — файл валиден
    {"ok": False, "error_type": 2, "detail": "..."} — повреждён или защищён
    """
    try:
        reader = PyPDF2.PdfReader(file_path)
        if reader.is_encrypted:
            return {"ok": False, "error_type": 2, "detail": "PDF защищён паролем"}
        _ = len(reader.pages)  # пробуем прочитать страницы
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error_type": 2, "detail": str(e)}
```

**Пример вызова и результата:**
```python
>>> check_pdf_integrity("выписка_сбер.pdf")
{"ok": True}

>>> check_pdf_integrity("encrypted.pdf")
{"ok": False, "error_type": 2, "detail": "PDF защищён паролем"}

>>> check_pdf_integrity("corrupted.pdf")
{"ok": False, "error_type": 2, "detail": "EOF marker not found"}
```

### 2. Извлечение текста со всех страниц

**Вход:** путь к файлу (str)
**Выход:** полный текст документа (str) или ошибка

```python
import pdfplumber

def extract_text_from_pdf(file_path: str) -> dict:
    """
    Возвращает:
    {"ok": True, "text": "...", "pages": 5}
    {"ok": False, "error_type": 3, "detail": "Нет текстового слоя"}
    """
    try:
        full_text = ""
        with pdfplumber.open(file_path) as pdf:
            page_count = len(pdf.pages)
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"

        # Проверка на скан (< 50 символов на первых 3 страницах)
        cleaned = full_text.replace(" ", "").replace("\n", "")
        if len(cleaned) < 50:
            return {
                "ok": False,
                "error_type": 3,
                "detail": f"Извлечено только {len(cleaned)} символов"
            }

        return {"ok": True, "text": full_text, "pages": page_count}

    except Exception as e:
        return {"ok": False, "error_type": 2, "detail": str(e)}
```

**Пример вызова и результата:**
```python
>>> result = extract_text_from_pdf("sber_march_2024.pdf")
>>> result["ok"]
True
>>> result["pages"]
3
>>> print(result["text"][:500])
"""
ПАО Сбербанк
Выписка по счёту 40817810000000000001
За период с 01.03.2024 по 31.03.2024
Клиент: Иванов Иван Иванович

Дата        Описание операции                   Сумма (руб.)
01.03.2024  Покупка ПЯТЕРОЧКА 1234              -1 250,00
02.03.2024  Покупка ЯНДЕКС.ТАКСИ                -350,00
03.03.2024  Пополнение Зарплата ООО Рога        +85 000,00
05.03.2024  Покупка АПТЕКА ОЗЕРКИ               -890,50
...
Исходящий остаток: 75 000,50 руб.
"""
```

### 3. Извлечение таблиц (альтернативный метод)

**Когда использовать:** если `extract_text()` не сохраняет структуру колонок.

```python
def extract_tables_from_pdf(file_path: str) -> list:
    """
    Возвращает список таблиц, каждая таблица — список строк,
    каждая строка — список ячеек.
    """
    tables = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            if page_tables:
                tables.extend(page_tables)
    return tables
```

**Пример результата:**
```python
>>> tables = extract_tables_from_pdf("tinkoff_april.pdf")
>>> tables[0][:3]  # первые 3 строки первой таблицы
[
    ["Дата", "Описание", "Категория", "Сумма"],
    ["01.04.2024", "ПЯТЕРОЧКА", "Супермаркеты", "-2 150,00"],
    ["01.04.2024", "ЯНДЕКС ТАКСИ", "Транспорт", "-450,00"]
]
```

## Типичные проблемы и решения

### Проблема: Текст из колонок слипается
```
# Вместо: "01.03.2024  ПЯТЕРОЧКА  -1250,00"
# Получаем: "01.03.2024ПЯТЕРОЧКА-1250,00"
```
**Решение:** Использовать `page.extract_text(x_tolerance=3, y_tolerance=3)` или переключиться на `extract_tables()`.

### Проблема: pdfplumber извлекает текст из шапок/колонтитулов
```python
# Обрезать область страницы (crop)
page_cropped = page.crop((0, 100, page.width, page.height - 50))
text = page_cropped.extract_text()
```

### Проблема: Кодировка — кракозябры вместо кириллицы
**Причина:** PDF использует нестандартные шрифты без Unicode-маппинга.
**Решение:** Это Ошибка Тип 3 — сообщить пользователю. pdfplumber не может декодировать такие PDF.

## Формат данных: Что получаем → что передаём дальше

```
pdfplumber.open(path)
    │
    ▼
page.extract_text() → str (многострочный текст)
    │
    ├──→ Balance Finder (Этап 2): ищет "Исходящий остаток: XXX руб."
    │
    └──→ Transaction Parser (Этап 3): ищет строки формата "ДД.ММ.ГГГГ описание сумма"
```

## Ограничения

- Не работает со сканами (PDF без текстового слоя) → на этот случай Этап 5 (OCR)
- Не открывает PDF, защищённые паролем → Ошибка Тип 2
- Максимальный размер файла: ограничен ОЗУ (~500 МБ PDF начнут тормозить)
- Время обработки: ~0.5-2 сек на файл 10-50 страниц
