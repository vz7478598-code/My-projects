# 02. Tesseract OCR — Распознавание текста с изображений

## Назначение в проекте

Локальный OCR-движок для распознавания текста со скриншотов и фотографий банковских выписок. Используется на **Этапе 5**. Принимает предобработанное изображение, возвращает текст, который затем передаётся в те же модули анализа, что и текст из PDF.

## Установка

### Windows (целевая ОС)
```bash
# 1. Скачать установщик Tesseract
# https://github.com/UB-Mannheim/tesseract/wiki
# Установить в C:\Program Files\Tesseract-OCR\

# 2. При установке выбрать языковые пакеты: Russian (rus) + English (eng)
# Или скачать отдельно в tessdata:
# https://github.com/tesseract-ocr/tessdata_best/raw/main/rus.traineddata

# 3. Добавить в PATH:
# C:\Program Files\Tesseract-OCR\

# 4. Python-обёртка:
pip install pytesseract==0.3.13
```

### Проверка установки
```bash
# Командная строка
tesseract --version
# tesseract 5.3.4
#  leptonica-1.84.1

tesseract --list-langs
# List of available languages (3):
# eng
# osd
# rus
```

## API: Командная строка (curl-аналог)

### Базовое распознавание

```bash
# Вход: изображение PNG/JPG
# Выход: текстовый файл

tesseract screenshot.png output -l rus+eng --psm 6

# Параметры:
# -l rus+eng      — языки (русский + английский)
# --psm 6         — режим сегментации: "единый блок текста"
# output          — имя выходного файла (создаст output.txt)
```

**Результат (output.txt):**
```
ПАО Сбербанк
Выписка по счёту 40817810000000000001
За период с 01.03.2024 по 31.03.2024

Дата        Описание операции         Сумма
01.03.2024  Покупка ПЯТЕРОЧКА         -1 250,00
02.03.2024  Покупка ЯНДЕКС.ТАКСИ      -350,00
Исходящий остаток: 75 000,50 руб.
```

### Вывод в stdout (без файла)

```bash
tesseract screenshot.png stdout -l rus+eng --psm 6
```

### С тонкой настройкой для цифр

```bash
tesseract screenshot.png stdout -l rus+eng --psm 6 \
  -c tessedit_char_whitelist="0123456789., -₽$€руб" \
  --oem 1
# --oem 1  — LSTM neural net (лучшее качество)
```

## API: Python (pytesseract)

### Базовое распознавание

**Вход:** PIL.Image (или путь к файлу)
**Выход:** str (распознанный текст)

```python
import pytesseract
from PIL import Image

# Указать путь к Tesseract (Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def ocr_image(image_path: str) -> dict:
    """
    Распознаёт текст с изображения.

    Возвращает:
    {"ok": True, "text": "...", "confidence": 85.5}
    {"ok": False, "error_type": "ocr_empty", "detail": "..."}
    """
    try:
        img = Image.open(image_path)

        # Основной вызов
        text = pytesseract.image_to_string(
            img,
            lang='rus+eng',
            config='--psm 6 --oem 1'
        )

        # Проверка результата
        cleaned = text.strip().replace(" ", "").replace("\n", "")
        if len(cleaned) < 50:
            return {
                "ok": False,
                "error_type": "ocr_empty",
                "detail": f"Распознано только {len(cleaned)} символов"
            }

        return {"ok": True, "text": text.strip()}

    except pytesseract.TesseractNotFoundError:
        return {
            "ok": False,
            "error_type": "ocr_not_installed",
            "detail": "Tesseract не найден. Проверьте установку."
        }
    except Exception as e:
        return {"ok": False, "error_type": "ocr_error", "detail": str(e)}
```

**Пример вызова и результата:**
```python
>>> result = ocr_image("screenshot_sber.png")
>>> result["ok"]
True
>>> print(result["text"][:300])
"""
ПАО Сбербанк
Выписка по счёту 40817810000000000001

Дата        Описание             Сумма
01.03.2024  ПЯТЕРОЧКА            -1 250,00
02.03.2024  ЯНДЕКС.ТАКСИ         -350,00
Исходящий остаток: 75 000,50 руб.
"""
```

### Получение данных с уровнем уверенности (confidence)

```python
def ocr_with_confidence(image_path: str) -> dict:
    """
    Распознаёт текст и возвращает среднюю уверенность (0-100).
    """
    img = Image.open(image_path)

    # Получаем детальные данные (TSV-формат)
    data = pytesseract.image_to_data(
        img,
        lang='rus+eng',
        config='--psm 6 --oem 1',
        output_type=pytesseract.Output.DICT
    )

    # Считаем среднюю уверенность (исключаем -1 = не распознано)
    confidences = [c for c in data['conf'] if c > 0]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0

    # Собираем текст
    words = [data['text'][i] for i in range(len(data['text'])) if data['conf'][i] > 0]
    text = ' '.join(words)

    return {
        "ok": True,
        "text": text,
        "avg_confidence": round(avg_confidence, 1),
        "word_count": len(words)
    }
```

**Пример результата:**
```python
>>> ocr_with_confidence("clear_screenshot.png")
{
    "ok": True,
    "text": "ПАО Сбербанк Выписка по счёту ...",
    "avg_confidence": 91.3,
    "word_count": 145
}

>>> ocr_with_confidence("blurry_photo.jpg")
{
    "ok": True,
    "text": "ПАО С6ербанк Выписка п0 сч...",
    "avg_confidence": 52.1,
    "word_count": 89
}
```

## Режимы сегментации страницы (--psm)

| PSM | Описание | Когда использовать |
|-----|----------|-------------------|
| 3 | Полностью автоматическая сегментация (по умолчанию) | Общий случай |
| 4 | Одна колонка текста | Выписка в одну колонку |
| **6** | **Единый блок текста** | **Рекомендуется для выписок** |
| 7 | Одна строка текста | Распознавание одной суммы |
| 11 | Разреженный текст | Скриншот с пробелами между колонками |
| 13 | Raw line (без OSD) | Если другие режимы дают мусор |

**Рекомендация:** Начинать с PSM 6. Если результат плохой (колонки слипаются), пробовать PSM 4 или PSM 11.

## Типичные ошибки OCR и постобработка

### Частые замены символов

```python
OCR_CORRECTIONS = {
    # Цифры ↔ буквы (самые частые ошибки)
    "О": "0",   # русская О → ноль (в контексте чисел)
    "о": "0",
    "З": "3",   # русская З → тройка (в контексте чисел)
    "б": "6",   # русская б → шестёрка (в контексте чисел)
    "l": "1",   # латинская l → единица
    "I": "1",   # латинская I → единица
    "S": "5",   # латинская S → пятёрка (в контексте чисел)
    "B": "8",   # латинская B → восьмёрка (в контексте чисел)
}
```

### Постпроцессор: очистка текста

```python
import re

def postprocess_ocr_text(raw_text: str) -> str:
    """
    Очищает «сырой» текст OCR для передачи в модули аналитики.
    """
    text = raw_text

    # 1. Убрать множественные пробелы (но оставить переносы строк)
    text = re.sub(r'[ \t]+', ' ', text)

    # 2. Убрать множественные пустые строки
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 3. Исправить частые ошибки в суммах: "1 25О,ОО" → "1 250,00"
    def fix_amount(match):
        amount_str = match.group(0)
        amount_str = amount_str.replace('О', '0')  # рус О → 0
        amount_str = amount_str.replace('о', '0')  # рус о → 0
        amount_str = amount_str.replace('З', '3')  # рус З → 3
        amount_str = amount_str.replace('l', '1')  # лат l → 1
        return amount_str

    # Паттерн суммы: число с разделителями
    text = re.sub(
        r'[-]?\d[\d\s]*[.,]\d{2}',
        fix_amount,
        text
    )

    # 4. Нормализовать разделители в датах: "О1.ОЗ.2024" → "01.03.2024"
    def fix_date(match):
        date_str = match.group(0)
        date_str = date_str.replace('О', '0').replace('о', '0').replace('З', '3')
        return date_str

    text = re.sub(
        r'\d{1,2}[./-]\d{1,2}[./-]\d{2,4}',
        fix_date,
        text
    )

    return text.strip()
```

**Пример:**
```python
>>> raw = "О1.ОЗ.2024  ПЯТЕРОЧКА  -1 25О,ОО руб."
>>> postprocess_ocr_text(raw)
"01.03.2024 ПЯТЕРОЧКА -1 250,00 руб."
```

## Ограничения

- Качество сильно зависит от качества изображения (разрешение ≥ 300 DPI рекомендуется)
- Плохо работает с фотографиями «с рук» (блики, перспективные искажения)
- Время обработки: 2-10 сек на изображение 1-4 МП (зависит от CPU)
- Требует установки Tesseract отдельно от Python (не pip-пакет)
- Языковые модели (~15 МБ каждый) нужно установить отдельно

## Поток данных в проекте

```
Изображение (PNG/JPG)
    │
    ▼
OpenCV предобработка (03_OPENCV_PILLOW.md)
    │
    ▼
pytesseract.image_to_string(img, lang='rus+eng', config='--psm 6 --oem 1')
    │
    ▼
postprocess_ocr_text(raw_text)
    │
    ▼
Тот же текст (str), что и из pdfplumber → Balance Finder → Transaction Parser
```
