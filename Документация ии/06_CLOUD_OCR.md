# 06. Cloud OCR — Облачные сервисы распознавания текста

## Назначение в проекте

Альтернатива локальному Tesseract для случаев, когда нужно более высокое качество распознавания. Используется на **Этапе 5** (опционально). Все сервисы работают через HTTP API — отправляем изображение, получаем текст.

**ВНИМАНИЕ:** Банковские выписки содержат персональные и финансовые данные. Использование облачных сервисов требует явного согласования с заказчиком и, возможно, NDA с провайдером.

## Варианты (по приоритету)

| Сервис | Качество кириллицы | Цена (ориентир) | Приватность |
|--------|-------------------|-----------------|-------------|
| Yandex Vision | Отличное | ~1.2₽/запрос | Серверы в РФ |
| Google Cloud Vision | Отличное | ~$1.50/1000 запросов | Серверы за рубежом |
| OCR.space | Хорошее | Бесплатно до 25K/мес | Серверы за рубежом |

---

## Вариант А: Yandex Vision OCR

### Аутентификация

```bash
# Получить IAM-токен (живёт 12 часов)
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"yandexPassportOauthToken": "YOUR_OAUTH_TOKEN"}' \
  https://iam.api.cloud.yandex.net/iam/v1/tokens
```

**Ответ:**
```json
{
  "iamToken": "t1.9euelZqYk5KMj5GTkp...",
  "expiresAt": "2024-04-05T18:30:00.000Z"
}
```

### Распознавание текста

**Запрос (curl):**
```bash
# Вход: изображение в base64
# Выход: распознанный текст

# 1. Кодируем изображение в base64
BASE64_IMAGE=$(base64 -w 0 screenshot.png)

# 2. Отправляем запрос
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_IAM_TOKEN" \
  -H "x-folder-id: YOUR_FOLDER_ID" \
  -d '{
    "mimeType": "image/png",
    "languageCodes": ["ru", "en"],
    "model": "page",
    "content": "'$BASE64_IMAGE'"
  }' \
  https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText
```

**Ответ (успех):**
```json
{
  "result": {
    "textAnnotation": {
      "fullText": "ПАО Сбербанк\nВыписка по счёту 40817810000000000001\nЗа период с 01.03.2024 по 31.03.2024\n\nДата        Описание             Сумма\n01.03.2024  ПЯТЕРОЧКА            -1 250,00\n02.03.2024  ЯНДЕКС.ТАКСИ         -350,00\nИсходящий остаток: 75 000,50 руб.",
      "pages": [
        {
          "width": "1920",
          "height": "1080",
          "blocks": [
            {
              "boundingBox": {
                "vertices": [
                  {"x": "50", "y": "30"},
                  {"x": "800", "y": "30"},
                  {"x": "800", "y": "70"},
                  {"x": "50", "y": "70"}
                ]
              },
              "lines": [
                {
                  "text": "ПАО Сбербанк",
                  "words": [
                    {"text": "ПАО", "confidence": 0.98},
                    {"text": "Сбербанк", "confidence": 0.99}
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  }
}
```

**Ответ (ошибка — превышен лимит):**
```json
{
  "code": 8,
  "message": "The request was throttled due to exceeding the quota.",
  "details": []
}
```

### Python-обёртка для Yandex Vision

```python
import requests
import base64
import json

YANDEX_OCR_URL = "https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText"

def yandex_ocr(image_path: str, iam_token: str, folder_id: str) -> dict:
    """
    Распознаёт текст через Yandex Vision OCR.

    Возвращает:
    {"ok": True, "text": "...", "confidence": 0.95}
    {"ok": False, "error_type": "...", "detail": "..."}
    """
    try:
        # Кодируем изображение
        with open(image_path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")

        # Определяем MIME-тип
        mime = "image/png" if image_path.lower().endswith(".png") else "image/jpeg"

        response = requests.post(
            YANDEX_OCR_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {iam_token}",
                "x-folder-id": folder_id
            },
            json={
                "mimeType": mime,
                "languageCodes": ["ru", "en"],
                "model": "page",
                "content": content
            },
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            full_text = data["result"]["textAnnotation"]["fullText"]

            # Средняя уверенность
            confidences = []
            for page in data["result"]["textAnnotation"]["pages"]:
                for block in page.get("blocks", []):
                    for line in block.get("lines", []):
                        for word in line.get("words", []):
                            if "confidence" in word:
                                confidences.append(word["confidence"])

            avg_conf = sum(confidences) / len(confidences) if confidences else 0

            return {"ok": True, "text": full_text, "confidence": round(avg_conf, 2)}

        elif response.status_code == 429:
            return {"ok": False, "error_type": "rate_limit",
                    "detail": "Превышен лимит запросов"}
        else:
            return {"ok": False, "error_type": "api_error",
                    "detail": f"HTTP {response.status_code}: {response.text[:200]}"}

    except requests.Timeout:
        return {"ok": False, "error_type": "timeout",
                "detail": "Превышено время ожидания (15 сек)"}
    except requests.ConnectionError:
        return {"ok": False, "error_type": "network",
                "detail": "Нет подключения к серверу"}
    except Exception as e:
        return {"ok": False, "error_type": "unknown", "detail": str(e)}
```

**Пример:**
```python
>>> result = yandex_ocr("screenshot.png", iam_token="t1.9euel...", folder_id="b1g...")
>>> result
{
    "ok": True,
    "text": "ПАО Сбербанк\nВыписка по счёту ...\nИсходящий остаток: 75 000,50 руб.",
    "confidence": 0.96
}
```

---

## Вариант Б: Google Cloud Vision

### Распознавание текста

**Запрос (curl):**
```bash
BASE64_IMAGE=$(base64 -w 0 screenshot.png)

curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "requests": [
      {
        "image": {
          "content": "'$BASE64_IMAGE'"
        },
        "features": [
          {
            "type": "TEXT_DETECTION",
            "maxResults": 1
          }
        ],
        "imageContext": {
          "languageHints": ["ru", "en"]
        }
      }
    ]
  }' \
  https://vision.googleapis.com/v1/images:annotate
```

**Ответ (успех):**
```json
{
  "responses": [
    {
      "textAnnotations": [
        {
          "locale": "ru",
          "description": "ПАО Сбербанк\nВыписка по счёту 40817810000000000001\nЗа период с 01.03.2024 по 31.03.2024\n\nДата Описание Сумма\n01.03.2024 ПЯТЕРОЧКА -1 250,00\n02.03.2024 ЯНДЕКС.ТАКСИ -350,00\nИсходящий остаток: 75 000,50 руб.\n",
          "boundingPoly": {
            "vertices": [
              {"x": 40, "y": 25},
              {"x": 850, "y": 25},
              {"x": 850, "y": 700},
              {"x": 40, "y": 700}
            ]
          }
        }
      ],
      "fullTextAnnotation": {
        "pages": [
          {
            "width": 1920,
            "height": 1080,
            "confidence": 0.97,
            "blocks": [...]
          }
        ],
        "text": "ПАО Сбербанк\nВыписка по счёту 40817810000000000001\n..."
      }
    }
  ]
}
```

**Ответ (ошибка):**
```json
{
  "error": {
    "code": 403,
    "message": "Cloud Vision API has not been used in project 123 before or it is disabled.",
    "status": "PERMISSION_DENIED"
  }
}
```

### Python-обёртка для Google Vision

```python
GOOGLE_VISION_URL = "https://vision.googleapis.com/v1/images:annotate"

def google_vision_ocr(image_path: str, api_key: str) -> dict:
    """
    Распознаёт текст через Google Cloud Vision.

    Возвращает:
    {"ok": True, "text": "...", "confidence": 0.97}
    {"ok": False, "error_type": "...", "detail": "..."}
    """
    try:
        with open(image_path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")

        response = requests.post(
            f"{GOOGLE_VISION_URL}?key={api_key}",
            json={
                "requests": [{
                    "image": {"content": content},
                    "features": [{"type": "TEXT_DETECTION"}],
                    "imageContext": {"languageHints": ["ru", "en"]}
                }]
            },
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            resp = data["responses"][0]

            if "error" in resp:
                return {"ok": False, "error_type": "api_error",
                        "detail": resp["error"]["message"]}

            if "fullTextAnnotation" not in resp:
                return {"ok": False, "error_type": "ocr_empty",
                        "detail": "Текст не распознан"}

            text = resp["fullTextAnnotation"]["text"]
            confidence = resp["fullTextAnnotation"]["pages"][0].get("confidence", 0)

            return {"ok": True, "text": text, "confidence": confidence}

        else:
            return {"ok": False, "error_type": "api_error",
                    "detail": f"HTTP {response.status_code}"}

    except requests.Timeout:
        return {"ok": False, "error_type": "timeout", "detail": "Таймаут 15 сек"}
    except Exception as e:
        return {"ok": False, "error_type": "unknown", "detail": str(e)}
```

---

## Вариант В: OCR.space (бесплатный)

### Распознавание текста

**Запрос (curl) — отправка файла:**
```bash
curl -X POST \
  -H "apikey: YOUR_API_KEY" \
  -F "file=@screenshot.png" \
  -F "language=rus" \
  -F "isOverlayRequired=false" \
  -F "OCREngine=2" \
  https://api.ocr.space/parse/image
```

**Запрос (curl) — отправка base64:**
```bash
BASE64_IMAGE=$(base64 -w 0 screenshot.png)

curl -X POST \
  -H "apikey: YOUR_API_KEY" \
  -d "base64Image=data:image/png;base64,$BASE64_IMAGE" \
  -d "language=rus" \
  -d "OCREngine=2" \
  https://api.ocr.space/parse/image
```

**Ответ (успех):**
```json
{
  "ParsedResults": [
    {
      "TextOverlay": null,
      "TextOrientation": "0",
      "FileParseExitCode": 1,
      "ParsedText": "ПАО Сбербанк\r\nВыписка по счёту 40817810000000000001\r\nЗа период с 01.03.2024 по 31.03.2024\r\n\r\nДата Описание Сумма\r\n01.03.2024 ПЯТЕРОЧКА -1 250,00\r\n02.03.2024 ЯНДЕКС.ТАКСИ -350,00\r\nИсходящий остаток: 75 000,50 руб.\r\n",
      "ErrorMessage": "",
      "ErrorDetails": ""
    }
  ],
  "OCRExitCode": 1,
  "IsErroredOnProcessing": false,
  "ProcessingTimeInMilliseconds": "1250",
  "SearchablePDFURL": null
}
```

**Ответ (ошибка — лимит):**
```json
{
  "OCRExitCode": 6,
  "IsErroredOnProcessing": true,
  "ErrorMessage": ["E216: You have exceeded the maximum number of free API calls."],
  "ProcessingTimeInMilliseconds": "0"
}
```

**Ответ (ошибка — файл слишком большой):**
```json
{
  "OCRExitCode": 6,
  "IsErroredOnProcessing": true,
  "ErrorMessage": ["E210: File too large. Maximum file size: 1024 KB for free plan."],
  "ProcessingTimeInMilliseconds": "0"
}
```

### Python-обёртка для OCR.space

```python
OCRSPACE_URL = "https://api.ocr.space/parse/image"

def ocrspace_ocr(image_path: str, api_key: str) -> dict:
    """
    Распознаёт текст через OCR.space (бесплатный сервис).

    Лимиты бесплатного плана:
    - 25 000 запросов/месяц
    - Максимум 1 МБ на файл
    - Engine 2 лучше для кириллицы

    Возвращает:
    {"ok": True, "text": "...", "processing_ms": 1250}
    {"ok": False, "error_type": "...", "detail": "..."}
    """
    try:
        with open(image_path, "rb") as f:
            response = requests.post(
                OCRSPACE_URL,
                files={"file": f},
                data={
                    "apikey": api_key,
                    "language": "rus",
                    "OCREngine": "2",
                    "isOverlayRequired": "false"
                },
                timeout=20
            )

        data = response.json()

        if data.get("IsErroredOnProcessing"):
            errors = data.get("ErrorMessage", ["Неизвестная ошибка"])
            error_msg = errors[0] if errors else "Неизвестная ошибка"

            if "E216" in error_msg:
                return {"ok": False, "error_type": "rate_limit", "detail": error_msg}
            elif "E210" in error_msg:
                return {"ok": False, "error_type": "file_too_large", "detail": error_msg}
            else:
                return {"ok": False, "error_type": "api_error", "detail": error_msg}

        parsed = data["ParsedResults"][0]
        text = parsed["ParsedText"].replace("\r\n", "\n").strip()

        if not text or len(text) < 20:
            return {"ok": False, "error_type": "ocr_empty",
                    "detail": "Текст не распознан или слишком короткий"}

        return {
            "ok": True,
            "text": text,
            "processing_ms": int(data.get("ProcessingTimeInMilliseconds", 0))
        }

    except requests.Timeout:
        return {"ok": False, "error_type": "timeout", "detail": "Таймаут 20 сек"}
    except Exception as e:
        return {"ok": False, "error_type": "unknown", "detail": str(e)}
```

---

## Единый адаптер (переключение между движками)

```python
def ocr_recognize(image_path: str, engine: str = "tesseract",
                   config: dict = None) -> dict:
    """
    Единый интерфейс для всех OCR-движков.
    engine: "tesseract" | "yandex" | "google" | "ocrspace"

    Всегда возвращает:
    {"ok": True/False, "text": str, ...}
    """
    config = config or {}

    if engine == "tesseract":
        return ocr_image(image_path)  # из 02_TESSERACT_OCR.md

    elif engine == "yandex":
        return yandex_ocr(
            image_path,
            iam_token=config["yandex_iam_token"],
            folder_id=config["yandex_folder_id"]
        )

    elif engine == "google":
        return google_vision_ocr(
            image_path,
            api_key=config["google_api_key"]
        )

    elif engine == "ocrspace":
        return ocrspace_ocr(
            image_path,
            api_key=config["ocrspace_api_key"]
        )

    else:
        return {"ok": False, "error_type": "unknown_engine",
                "detail": f"Неизвестный OCR-движок: {engine}"}
```

**Конфигурация (config.ini):**
```ini
[ocr]
engine = tesseract          # tesseract | yandex | google | ocrspace

[yandex]
oauth_token = y0_AgAAAA...
folder_id = b1g12345...

[google]
api_key = AIzaSy...

[ocrspace]
api_key = K12345...
```

## Сравнение качества на реальных примерах

| Текст на скриншоте | Tesseract | Yandex | Google |
|-------------------|-----------|--------|--------|
| `75 000,50 руб.` | `75 0О0,5О руб.` ❌ | `75 000,50 руб.` ✅ | `75 000,50 руб.` ✅ |
| `ПЯТЕРОЧКА` | `ПЯТЕРОЧКА` ✅ | `ПЯТЕРОЧКА` ✅ | `ПЯТЕРОЧКА` ✅ |
| `01.03.2024` | `О1.ОЗ.2О24` ❌ | `01.03.2024` ✅ | `01.03.2024` ✅ |
| Фото с бликами | Мусор ❌ | Читаемо ⚠️ | Читаемо ⚠️ |

**Вывод:** Для MVP начинать с Tesseract + постобработка. Если качество недостаточно — переключить на Yandex Vision через конфиг.
