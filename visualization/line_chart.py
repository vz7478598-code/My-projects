"""Генерация линейных графиков динамики расходов/доходов."""

import os
import tempfile
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

matplotlib.rcParams["font.family"] = "DejaVu Sans"


def generate_line_chart(
    records: list,
    output_path: str = None,
    title: str = "Динамика расходов",
) -> dict:
    """Строит линейный график расходов, доходов и баланса по периодам.

    Args:
        records: список записей из get_history.
        output_path: путь для сохранения PNG. Если None — временный файл.
        title: заголовок графика.

    Returns:
        dict с результатом: {"ok": True, "path": "..."} или ошибка.
    """
    if not records or len(records) < 2:
        return {
            "ok": False,
            "error_type": "not_enough_data",
            "detail": "Нужно минимум 2 периода",
        }

    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(tempfile.gettempdir(), f"line_chart_{ts}.png")

    periods = [r["period_key"] for r in records]
    expenses = [r["total_expense"] for r in records]
    incomes = [r["total_income"] for r in records]

    has_balance = any(r.get("total_balance") is not None for r in records)
    if has_balance:
        balances = [r.get("total_balance", 0) or 0 for r in records]

    plt.figure(figsize=(10, 6))

    plt.plot(periods, expenses, color="red", label="Расходы", marker="o")
    plt.plot(periods, incomes, color="green", label="Доходы", marker="s")

    if has_balance:
        plt.plot(
            periods, balances, color="blue", label="Баланс",
            marker="^", linestyle="--",
        )

    plt.xlabel("Период")
    plt.ylabel("Сумма (руб.)")
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    return {"ok": True, "path": output_path}
