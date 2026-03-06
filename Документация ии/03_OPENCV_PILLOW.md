# 03. OpenCV + Pillow — Предобработка изображений

## Назначение в проекте

Подготовка изображений (скриншотов, фотографий) перед подачей в Tesseract OCR. Без предобработки качество распознавания резко падает. Используется на **Этапе 5**.

## Установка

```bash
pip install opencv-python==4.9.0.80   # основной пакет (без GUI)
pip install Pillow==10.4.0             # работа с форматами изображений
```

## Зачем нужны обе библиотеки

- **Pillow (PIL)** — открытие/сохранение изображений, определение формата, базовые операции, интерфейс для pytesseract
- **OpenCV** — продвинутая обработка: бинаризация, шумоподавление, выравнивание перекоса (deskew)

## API: Полный конвейер предобработки

### Общая функция (вход → выход)

**Вход:** путь к файлу изображения (str)
**Выход:** предобработанный PIL.Image, готовый для OCR

```python
import cv2
import numpy as np
from PIL import Image

def preprocess_for_ocr(image_path: str) -> dict:
    """
    Полный конвейер предобработки изображения для OCR.

    Возвращает:
    {"ok": True, "image": PIL.Image, "steps_applied": [...]}
    {"ok": False, "error_type": "...", "detail": "..."}
    """
    try:
        # 1. Загрузка и валидация
        img = cv2.imread(image_path)
        if img is None:
            return {"ok": False, "error_type": "image_corrupted",
                    "detail": "Не удалось открыть изображение"}

        h, w = img.shape[:2]
        steps = []

        # 2. Проверка размеров
        max_pixels = 20_000_000  # ~20 МП
        if h * w > max_pixels:
            return {"ok": False, "error_type": "image_too_large",
                    "detail": f"Разрешение {w}x{h} превышает лимит"}

        # 3. Конвертация в оттенки серого
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        steps.append("grayscale")

        # 4. Масштабирование (если изображение маленькое)
        if h < 1000 or w < 1000:
            scale = 2.0
            gray = cv2.resize(gray, None, fx=scale, fy=scale,
                             interpolation=cv2.INTER_CUBIC)
            steps.append(f"upscale_x{scale}")

        # 5. Шумоподавление (медианная фильтрация)
        denoised = cv2.medianBlur(gray, 3)
        steps.append("denoise_median")

        # 6. Адаптивная бинаризация
        binary = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=11,
            C=2
        )
        steps.append("adaptive_threshold")

        # 7. Выравнивание перекоса (deskew)
        angle = detect_skew_angle(binary)
        if abs(angle) > 0.5:  # поворачиваем только если перекос > 0.5°
            binary = rotate_image(binary, angle)
            steps.append(f"deskew_{angle:.1f}deg")

        # 8. Конвертация обратно в PIL для pytesseract
        pil_image = Image.fromarray(binary)

        return {"ok": True, "image": pil_image, "steps_applied": steps}

    except Exception as e:
        return {"ok": False, "error_type": "preprocess_error",
                "detail": str(e)}
```

**Пример вызова:**
```python
>>> result = preprocess_for_ocr("screenshot_tinkoff.png")
>>> result["ok"]
True
>>> result["steps_applied"]
["grayscale", "denoise_median", "adaptive_threshold"]

>>> result = preprocess_for_ocr("blurry_photo.jpg")
>>> result["ok"]
True
>>> result["steps_applied"]
["grayscale", "upscale_x2.0", "denoise_median", "adaptive_threshold", "deskew_1.3deg"]
```

### Детальные операции

#### 3a. Конвертация в grayscale

```python
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
```

**Вход:** numpy array shape (H, W, 3) — цветное изображение BGR
**Выход:** numpy array shape (H, W) — одноканальное изображение

#### 3b. Масштабирование

```python
# Увеличение в 2 раза (для мелких скриншотов)
scaled = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

# Уменьшение (для огромных фото)
scaled = cv2.resize(gray, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
```

**Когда масштабировать:**
- Высота < 1000px или ширина < 1000px → увеличить x2
- Высота > 5000px → уменьшить до ~3000px по высоте

#### 3c. Шумоподавление

```python
# Медианный фильтр (лучше для «соль-перец» шума)
denoised = cv2.medianBlur(gray, 3)  # kernel_size=3 (всегда нечётное)

# Гауссов фильтр (мягче, для общего шума)
denoised = cv2.GaussianBlur(gray, (3, 3), 0)

# Билатеральный фильтр (сохраняет края текста)
denoised = cv2.bilateralFilter(gray, 9, 75, 75)
```

**Рекомендация:** medianBlur(3) — оптимальный баланс для скриншотов. Для фотографий с телефона — bilateralFilter.

#### 3d. Бинаризация (чёрно-белое)

```python
# Вариант 1: Адаптивный порог (РЕКОМЕНДУЕТСЯ для выписок)
binary = cv2.adaptiveThreshold(
    denoised,
    maxValue=255,
    adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    thresholdType=cv2.THRESH_BINARY,
    blockSize=11,    # размер окна (нечётное, 11-31)
    C=2              # константа вычитания (2-10)
)

# Вариант 2: Метод Оцу (автоматический глобальный порог)
_, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
```

**Когда какой:**
- Скриншот с равномерным фоном → Оцу (проще, быстрее)
- Фото экрана с бликами → Адаптивный (справляется с неравномерным освещением)

#### 3e. Определение и исправление перекоса (deskew)

```python
def detect_skew_angle(binary_image: np.ndarray) -> float:
    """
    Определяет угол перекоса текста в градусах.
    Положительный = повернут по часовой стрелке.
    """
    coords = np.column_stack(np.where(binary_image < 128))  # чёрные пиксели
    if len(coords) < 100:
        return 0.0
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    return angle

def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
    """
    Поворачивает изображение на заданный угол с сохранением размера.
    """
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    return rotated
```

**Пример:**
```python
>>> angle = detect_skew_angle(binary)
>>> angle
1.3  # текст повёрнут на 1.3° по часовой

>>> corrected = rotate_image(binary, angle)
# Теперь текст выровнен горизонтально
```

## Валидация изображения (Pillow)

```python
from PIL import Image
import os

def validate_image(file_path: str) -> dict:
    """
    Проверяет, что файл — корректное изображение в поддерживаемом формате.

    Возвращает:
    {"ok": True, "format": "PNG", "size_mb": 1.5, "resolution": (1920, 1080)}
    {"ok": False, "error_type": "...", "detail": "..."}
    """
    MAX_FILE_SIZE_MB = 10
    MAX_RESOLUTION = (8000, 8000)

    try:
        # Проверка размера файла
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            return {"ok": False, "error_type": "image_too_large",
                    "detail": f"Размер файла {size_mb:.1f} МБ превышает лимит {MAX_FILE_SIZE_MB} МБ"}

        # Проверка формата и целостности
        img = Image.open(file_path)
        img.verify()  # проверяет целостность, не загружая полностью

        # Повторное открытие после verify()
        img = Image.open(file_path)
        fmt = img.format  # "PNG", "JPEG"
        w, h = img.size

        if fmt not in ("PNG", "JPEG"):
            return {"ok": False, "error_type": "unsupported_format",
                    "detail": f"Формат {fmt} не поддерживается. Используйте PNG или JPG"}

        if w > MAX_RESOLUTION[0] or h > MAX_RESOLUTION[1]:
            return {"ok": False, "error_type": "image_too_large",
                    "detail": f"Разрешение {w}x{h} превышает лимит"}

        return {"ok": True, "format": fmt, "size_mb": round(size_mb, 1),
                "resolution": (w, h)}

    except (IOError, SyntaxError) as e:
        return {"ok": False, "error_type": "image_corrupted",
                "detail": f"Файл повреждён или не является изображением: {e}"}
```

**Примеры:**
```python
>>> validate_image("screenshot.png")
{"ok": True, "format": "PNG", "size_mb": 0.8, "resolution": (1920, 1080)}

>>> validate_image("huge_photo.jpg")
{"ok": False, "error_type": "image_too_large", "detail": "Размер файла 15.3 МБ превышает лимит 10 МБ"}

>>> validate_image("document.docx")
{"ok": False, "error_type": "image_corrupted", "detail": "Файл повреждён или не является изображением: ..."}
```

## Определение типа файла по сигнатуре

```python
def detect_file_type(file_path: str) -> str:
    """
    Определяет тип файла по магическим байтам (первые 8 байт).

    Возвращает: "pdf", "png", "jpeg", "unknown"
    """
    SIGNATURES = {
        b'%PDF':              "pdf",
        b'\x89PNG\r\n\x1a\n': "png",
        b'\xff\xd8\xff':       "jpeg",
    }

    with open(file_path, 'rb') as f:
        header = f.read(8)

    for sig, file_type in SIGNATURES.items():
        if header.startswith(sig):
            return file_type

    return "unknown"
```

```python
>>> detect_file_type("выписка.pdf")
"pdf"
>>> detect_file_type("screenshot.png")
"png"
>>> detect_file_type("photo.jpg")
"jpeg"
>>> detect_file_type("document.docx")
"unknown"
```

## Поток данных

```
Файл пользователя
    │
    ▼
detect_file_type() → "png" / "jpeg"
    │
    ▼
validate_image() → ok? формат? размер?
    │
    ▼
preprocess_for_ocr() → PIL.Image (бинаризованный)
    │
    ▼
pytesseract.image_to_string(image) → str (02_TESSERACT_OCR.md)
```

## Ограничения

- OpenCV не поддерживает HEIC (фото с iPhone) напрямую → нужен конвертер или pillow-heif
- Бинаризация может «убить» тонкий текст мелким шрифтом → настройка blockSize и C
- Deskew не справляется с перспективными искажениями (фото под углом) → нужна гомография (выходит за рамки MVP)
