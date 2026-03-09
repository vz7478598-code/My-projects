"""Анализ трендов расходов/доходов по периодам."""


def analyze_trends(records: list) -> dict:
    """Анализирует тренды на основе последних двух периодов.

    Args:
        records: список записей из get_history, отсортированный по period_key ASC.

    Returns:
        dict с результатами анализа или ошибкой.
    """
    if not records or len(records) < 2:
        return {
            "ok": False,
            "error_type": "not_enough_data",
            "detail": "Нужно минимум 2 периода для анализа трендов",
        }

    previous = records[-2]
    current = records[-1]

    expense_change = current["total_expense"] - previous["total_expense"]
    if previous["total_expense"] != 0:
        expense_change_pct = (expense_change / previous["total_expense"]) * 100
    else:
        expense_change_pct = 0

    income_change = current["total_income"] - previous["total_income"]
    if previous["total_income"] != 0:
        income_change_pct = (income_change / previous["total_income"]) * 100
    else:
        income_change_pct = 0

    balance_change = None
    if current.get("total_balance") is not None and previous.get("total_balance") is not None:
        balance_change = current["total_balance"] - previous["total_balance"]

    # Сравнение категорий
    cur_cats = current.get("categories") or {}
    prev_cats = previous.get("categories") or {}
    all_categories = set(cur_cats.keys()) | set(prev_cats.keys())

    category_changes = []
    anomalies = []
    for cat in all_categories:
        cur_val = cur_cats.get(cat, 0)
        prev_val = prev_cats.get(cat, 0)
        change = cur_val - prev_val
        if prev_val != 0:
            change_pct = (change / prev_val) * 100
        else:
            change_pct = 0

        entry = {
            "category": cat,
            "current": cur_val,
            "previous": prev_val,
            "change": change,
            "change_pct": round(change_pct, 1),
        }
        category_changes.append(entry)

        if abs(change_pct) > 500:
            anomalies.append(entry)

    category_changes.sort(key=lambda x: abs(x["change"]), reverse=True)
    anomalies.sort(key=lambda x: abs(x["change_pct"]), reverse=True)

    return {
        "ok": True,
        "current_period": current["period_key"],
        "previous_period": previous["period_key"],
        "expense_change": expense_change,
        "expense_change_pct": round(expense_change_pct, 1),
        "income_change": income_change,
        "income_change_pct": round(income_change_pct, 1),
        "balance_change": balance_change,
        "category_changes": category_changes,
        "anomalies": anomalies,
    }


def _format_amount(amount: float) -> str:
    """Форматирует сумму с разделителями тысяч и запятой для дробной части."""
    return f"{amount:,.2f}".replace(",", " ").replace(".", ",")


def generate_trend_comment(trend_data: dict) -> str:
    """Генерирует текстовый комментарий по результатам анализа трендов.

    Args:
        trend_data: результат analyze_trends (с ok=True).

    Returns:
        Текстовый комментарий на русском языке.
    """
    if not trend_data.get("ok"):
        return trend_data.get("detail", "Недостаточно данных для анализа.")

    parts = []

    cur = trend_data["current_period"]
    prev = trend_data["previous_period"]
    exp_pct = trend_data["expense_change_pct"]
    exp_change = trend_data["expense_change"]

    if exp_change > 0:
        parts.append(
            f"Расходы за {cur} выросли на {abs(exp_pct):.1f}% "
            f"по сравнению с {prev} (+{_format_amount(exp_change)} руб.)."
        )
    elif exp_change < 0:
        parts.append(
            f"Расходы за {cur} снизились на {abs(exp_pct):.1f}% "
            f"по сравнению с {prev} (-{_format_amount(abs(exp_change))} руб.)."
        )
    else:
        parts.append(f"Расходы за {cur} не изменились по сравнению с {prev}.")

    # Категории: выросшие и снизившиеся
    changes = trend_data.get("category_changes", [])
    grown = [c for c in changes if c["change"] > 0]
    reduced = [c for c in changes if c["change"] < 0]

    if grown:
        items = ", ".join(
            f"{c['category']} (+{abs(c['change_pct']):.1f}%)" for c in grown[:3]
        )
        parts.append(f"Больше всего выросли: {items}.")

    if reduced:
        items = ", ".join(
            f"{c['category']} (-{abs(c['change_pct']):.1f}%)" for c in reduced[:3]
        )
        parts.append(f"Снизились: {items}.")

    # Аномалии
    for a in trend_data.get("anomalies", []):
        sign = "+" if a["change_pct"] > 0 else ""
        parts.append(
            f"\u26a0 Аномальное изменение: {a['category']} ({sign}{a['change_pct']:.0f}%)"
        )

    return "\n".join(parts)
