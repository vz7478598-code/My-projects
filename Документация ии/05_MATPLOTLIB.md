# 05. Matplotlib — Визуализация (диаграммы и графики)

## Назначение в проекте

Библиотека для генерации графиков в виде PNG-изображений, которые встраиваются в чат как сообщения. Используется на **Этапах 3–4**:
- **Этап 3:** Круговая диаграмма расходов по категориям
- **Этап 4:** Линейный график трендов расходов по месяцам

## Установка

```bash
pip install matplotlib==3.9.2
```

**Важно для Windows десктопа:** Matplotlib использует бэкенд `Agg` (без GUI), так как графики сохраняются в файл, а не показываются в окне.

```python
import matplotlib
matplotlib.use('Agg')  # ОБЯЗАТЕЛЬНО до импорта pyplot
import matplotlib.pyplot as plt
```

## API: Круговая диаграмма (Этап 3)

### Функция генерации

**Вход:** словарь `{категория: сумма}`
**Выход:** путь к PNG-файлу

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import tempfile

# Настройка шрифтов для кириллицы
plt.rcParams['font.family'] = 'DejaVu Sans'  # поддерживает кириллицу из коробки

# Цветовая палитра (контрастная, эстетичная)
CATEGORY_COLORS = {
    "Продукты":          "#4CAF50",  # зелёный
    "Транспорт":         "#2196F3",  # синий
    "Кафе и рестораны":  "#FF9800",  # оранжевый
    "ЖКХ и связь":       "#9C27B0",  # фиолетовый
    "Здоровье":          "#F44336",  # красный
    "Переводы":          "#607D8B",  # серо-синий
    "Другое":            "#795548",  # коричневый
}

DEFAULT_COLORS = ["#4CAF50", "#2196F3", "#FF9800", "#9C27B0",
                  "#F44336", "#607D8B", "#795548", "#00BCD4",
                  "#E91E63", "#CDDC39"]


def generate_pie_chart(categories: dict, output_path: str = None,
                       dark_mode: bool = False) -> dict:
    """
    Генерирует круговую диаграмму расходов.

    Вход:
    categories = {"Продукты": 15420.50, "Транспорт": 3050.00, ...}
    dark_mode = True/False (подстройка под тему ОС)

    Возвращает:
    {"ok": True, "path": "/tmp/pie_chart_abc123.png", "total": 45520.50}
    {"ok": False, "error": "..."}
    """
    try:
        if not categories or all(v == 0 for v in categories.values()):
            return {"ok": False, "error": "Нет данных для диаграммы"}

        # Фильтрация нулевых категорий
        data = {k: v for k, v in categories.items() if v > 0}

        labels = list(data.keys())
        values = list(data.values())
        total = sum(values)

        # Цвета
        colors = [CATEGORY_COLORS.get(label, DEFAULT_COLORS[i % len(DEFAULT_COLORS)])
                  for i, label in enumerate(labels)]

        # Настройка фигуры
        fig, ax = plt.subplots(figsize=(8, 6), facecolor='#1E1E1E' if dark_mode else 'white')
        ax.set_facecolor('#1E1E1E' if dark_mode else 'white')
        text_color = 'white' if dark_mode else 'black'

        # Круговая диаграмма
        wedges, texts, autotexts = ax.pie(
            values,
            labels=None,         # подписи в легенде, не на секторах
            autopct='%1.1f%%',   # проценты на секторах
            colors=colors,
            startangle=90,
            pctdistance=0.75,
            wedgeprops={'edgecolor': '#1E1E1E' if dark_mode else 'white',
                        'linewidth': 2}
        )

        # Стиль процентов
        for autotext in autotexts:
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')
            autotext.set_color('white')

        # Легенда с суммами
        legend_labels = [
            f"{label}: {value:,.0f} ₽".replace(",", " ")
            for label, value in zip(labels, values)
        ]
        legend = ax.legend(
            wedges, legend_labels,
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1),
            fontsize=10
        )
        legend.get_frame().set_facecolor('#2D2D2D' if dark_mode else '#F5F5F5')
        for text in legend.get_texts():
            text.set_color(text_color)

        # Заголовок
        ax.set_title(
            f"Расходы: {total:,.0f} ₽".replace(",", " "),
            fontsize=14, fontweight='bold', color=text_color, pad=20
        )

        plt.tight_layout()

        # Сохранение
        if output_path is None:
            output_path = os.path.join(tempfile.gettempdir(),
                                        f"pie_chart_{id(fig)}.png")

        fig.savefig(output_path, dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        plt.close(fig)

        return {"ok": True, "path": output_path, "total": total}

    except Exception as e:
        plt.close('all')
        return {"ok": False, "error": str(e)}
```

**Пример вызова:**
```python
>>> result = generate_pie_chart({
...     "Продукты": 15420.50,
...     "Транспорт": 3050.00,
...     "Кафе и рестораны": 5200.00,
...     "ЖКХ и связь": 8500.00,
...     "Здоровье": 1200.00,
...     "Переводы": 10000.00,
...     "Другое": 2150.00
... }, dark_mode=False)

>>> result
{
    "ok": True,
    "path": "/tmp/pie_chart_140234567890.png",
    "total": 45520.50
}
# Файл: PNG 1200x900px, круговая диаграмма с 7 секторами,
# легенда справа с суммами, заголовок "Расходы: 45 520 ₽"
```

## API: Линейный график трендов (Этап 4)

### Функция генерации

**Вход:** список записей из SQLite (см. `04_SQLITE.md` → `get_history()`)
**Выход:** путь к PNG-файлу

```python
def generate_trend_chart(records: list, max_categories: int = 7,
                          output_path: str = None,
                          dark_mode: bool = False) -> dict:
    """
    Генерирует линейный график трендов расходов по категориям.

    Вход:
    records = [
        {"period_key": "2024-01", "categories": {"Продукты": 12000, "Транспорт": 4000, ...}},
        {"period_key": "2024-02", "categories": {"Продукты": 14000, "Транспорт": 3500, ...}},
        {"period_key": "2024-03", "categories": {"Продукты": 15420, "Транспорт": 3050, ...}},
    ]
    max_categories = 7 (остальные агрегируются в «Остальное»)

    Возвращает:
    {"ok": True, "path": "...", "periods": 3, "categories_shown": 5}
    {"ok": False, "error": "Недостаточно данных (нужно >= 2 периодов)"}
    """
    try:
        if len(records) < 2:
            return {"ok": False,
                    "error": "Недостаточно данных (нужно >= 2 периодов)"}

        # Собираем все категории и их суммарные расходы
        all_categories = {}
        for rec in records:
            for cat, amount in rec["categories"].items():
                all_categories[cat] = all_categories.get(cat, 0) + amount

        # Топ-N категорий по сумме
        sorted_cats = sorted(all_categories.items(), key=lambda x: x[1], reverse=True)
        top_cats = [cat for cat, _ in sorted_cats[:max_categories]]
        has_other = len(sorted_cats) > max_categories

        # Подготовка данных
        periods = [rec["period_key"] for rec in records]
        # Формат периодов: "2024-01" → "Янв 24"
        month_names = {
            "01": "Янв", "02": "Фев", "03": "Мар", "04": "Апр",
            "05": "Май", "06": "Июн", "07": "Июл", "08": "Авг",
            "09": "Сен", "10": "Окт", "11": "Ноя", "12": "Дек"
        }
        x_labels = []
        for p in periods:
            year, month = p.split("-")
            x_labels.append(f"{month_names.get(month, month)} {year[2:]}")

        # Данные по категориям
        category_data = {}
        for cat in top_cats:
            category_data[cat] = [
                rec["categories"].get(cat, 0) for rec in records
            ]

        if has_other:
            other_cats = [cat for cat, _ in sorted_cats[max_categories:]]
            category_data["Остальное"] = [
                sum(rec["categories"].get(cat, 0) for cat in other_cats)
                for rec in records
            ]

        # Построение графика
        fig, ax = plt.subplots(figsize=(10, 6),
                                facecolor='#1E1E1E' if dark_mode else 'white')
        ax.set_facecolor('#1E1E1E' if dark_mode else 'white')
        text_color = 'white' if dark_mode else 'black'
        grid_color = '#444444' if dark_mode else '#E0E0E0'

        x = range(len(periods))

        for cat_name, values in category_data.items():
            color = CATEGORY_COLORS.get(cat_name, None)
            line, = ax.plot(x, values, marker='o', linewidth=2,
                           markersize=6, label=cat_name, color=color)

        # Оформление
        ax.set_xticks(list(x))
        ax.set_xticklabels(x_labels, fontsize=10, color=text_color)
        ax.set_ylabel("Расходы, ₽", fontsize=12, color=text_color)
        ax.set_title("Динамика расходов по категориям", fontsize=14,
                     fontweight='bold', color=text_color, pad=15)

        ax.tick_params(colors=text_color)
        ax.grid(True, alpha=0.3, color=grid_color)

        # Форматирование оси Y (тысячи)
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, p: f"{x:,.0f}".replace(",", " "))
        )

        # Легенда
        legend = ax.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=10)
        legend.get_frame().set_facecolor('#2D2D2D' if dark_mode else '#F5F5F5')
        for text in legend.get_texts():
            text.set_color(text_color)

        for spine in ax.spines.values():
            spine.set_color(grid_color)

        plt.tight_layout()

        # Сохранение
        if output_path is None:
            output_path = os.path.join(tempfile.gettempdir(),
                                        f"trend_chart_{id(fig)}.png")

        fig.savefig(output_path, dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        plt.close(fig)

        return {
            "ok": True,
            "path": output_path,
            "periods": len(periods),
            "categories_shown": len(category_data)
        }

    except Exception as e:
        plt.close('all')
        return {"ok": False, "error": str(e)}
```

**Пример вызова:**
```python
>>> records = [
...     {"period_key": "2024-01", "categories": {"Продукты": 12000, "Транспорт": 4000, "Кафе и рестораны": 6000}},
...     {"period_key": "2024-02", "categories": {"Продукты": 14000, "Транспорт": 3500, "Кафе и рестораны": 7500}},
...     {"period_key": "2024-03", "categories": {"Продукты": 15420, "Транспорт": 3050, "Кафе и рестораны": 5200}},
... ]
>>> result = generate_trend_chart(records, dark_mode=False)
>>> result
{
    "ok": True,
    "path": "/tmp/trend_chart_140234567890.png",
    "periods": 3,
    "categories_shown": 3
}
# Файл: PNG 1500x900px, 3 линии (Продукты ↑, Транспорт ↓, Кафе ↗↘)
# Ось X: "Янв 24", "Фев 24", "Мар 24"
# Ось Y: суммы в рублях
# Легенда справа
```

## Генерация текстовых комментариев (Этап 4)

```python
def generate_trend_comment(current: dict, previous: dict,
                            anomaly_threshold: float = 500) -> str:
    """
    Сравнивает два периода и генерирует текстовый комментарий.

    Вход:
    current  = {"period_key": "2024-03", "total_expense": 45520.50,
                "categories": {"Продукты": 15420, "Транспорт": 3050, ...}}
    previous = {"period_key": "2024-02", "total_expense": 41000.00,
                "categories": {"Продукты": 14000, "Транспорт": 3500, ...}}

    Выход: str — текст для чата
    """
    comments = []

    # Общие расходы
    total_diff = current["total_expense"] - previous["total_expense"]
    if previous["total_expense"] > 0:
        total_pct = (total_diff / previous["total_expense"]) * 100
    else:
        total_pct = 0

    if abs(total_pct) < 3:
        comments.append("Общий уровень расходов остался стабильным.")
    elif total_diff > 0:
        comments.append(
            f"Общие расходы выросли на {abs(total_diff):,.0f} ₽ "
            f"({abs(total_pct):.0f}%).".replace(",", " ")
        )
    else:
        comments.append(
            f"Общие расходы снизились на {abs(total_diff):,.0f} ₽ "
            f"({abs(total_pct):.0f}%).".replace(",", " ")
        )

    # Категории с наибольшим изменением
    changes = []
    all_cats = set(list(current["categories"].keys()) +
                   list(previous["categories"].keys()))

    for cat in all_cats:
        cur_val = current["categories"].get(cat, 0)
        prev_val = previous["categories"].get(cat, 0)
        if prev_val == 0:
            continue
        pct = ((cur_val - prev_val) / prev_val) * 100
        if abs(pct) > anomaly_threshold:
            continue  # пропускаем аномалии
        changes.append({
            "category": cat,
            "abs_change": cur_val - prev_val,
            "pct_change": pct
        })

    if changes:
        # Наибольшее абсолютное изменение
        biggest = max(changes, key=lambda x: abs(x["abs_change"]))
        direction = "выросли" if biggest["abs_change"] > 0 else "снизились"
        comments.append(
            f"Траты на «{biggest['category']}» {direction} "
            f"на {abs(biggest['abs_change']):,.0f} ₽ "
            f"({abs(biggest['pct_change']):.0f}%).".replace(",", " ")
        )

    return " ".join(comments)
```

**Пример:**
```python
>>> generate_trend_comment(
...     current={"total_expense": 45520.50,
...              "categories": {"Продукты": 15420, "Транспорт": 3050, "Кафе": 5200}},
...     previous={"total_expense": 41000.00,
...               "categories": {"Продукты": 14000, "Транспорт": 3500, "Кафе": 7500}}
... )
"Общие расходы выросли на 4 520 ₽ (11%). Траты на «Кафе» снизились на 2 300 ₽ (31%)."
```

## Ограничения

- `matplotlib.use('Agg')` — обязательно вызвать до `import pyplot`, иначе на Windows без дисплея будет ошибка
- Шрифт DejaVu Sans поддерживает кириллицу, но некоторые системы могут его не иметь → запасной вариант: `plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']`
- Всегда вызывать `plt.close(fig)` после сохранения, иначе утечка памяти при многократной генерации
- PNG файлы занимают ~50-200 КБ каждый
