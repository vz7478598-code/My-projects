import os
import tempfile
from datetime import datetime

import matplotlib
import matplotlib.pyplot as plt

matplotlib.rcParams['font.family'] = 'DejaVu Sans'


def generate_pie_chart(
    categories: dict,
    output_path: str = None,
    title: str = "Расходы по категориям",
) -> dict:
    if not categories:
        return {"ok": False, "error_type": "no_data", "detail": "Нет данных для диаграммы"}

    sorted_items = sorted(categories.items(), key=lambda x: x[1], reverse=True)
    labels = []
    sizes = []
    for name, amount in sorted_items:
        labels.append(f"{name}\n({amount:,.0f} руб.)".replace(",", " "))
        sizes.append(amount)

    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(tempfile.gettempdir(), f"pie_chart_{ts}.png")

    colors = plt.cm.tab10.colors

    plt.figure(figsize=(8, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors[:len(sizes)])
    plt.title(title)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    return {"ok": True, "path": output_path}
