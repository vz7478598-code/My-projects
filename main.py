import os
import tkinter as tk
import threading
from datetime import datetime

from config import (
    DB_PATH,
    HISTORY_MONTHS,
    MAX_CHART_CATEGORIES,
)
from parsers.file_detector import detect_file_type
from parsers.pdf_parser import check_pdf_integrity, extract_text_from_pdf
from parsers.image_preprocessor import validate_image
from parsers.ocr_engine import ocr_image
from parsers.ocr_postprocessor import postprocess_ocr_text
from analyzers.balance_finder import find_balance
from analyzers.transaction_parser import parse_transactions
from analyzers.classifier import classify_transactions
from analyzers.aggregator import aggregate_expenses, limit_categories
from analyzers.trend_analyzer import analyze_trends, generate_trend_comment
from visualization.pie_chart import generate_pie_chart
from visualization.line_chart import generate_line_chart
from storage.database import init_db, save_statement, replace_statement, get_history
from gui.chat_window import ChatWindow
from utils.date_parser import extract_period


def process_file(file_path: str, chat: ChatWindow, db_conn):
    loading = None
    try:
        chat.add_message(f"Файл получен: {os.path.basename(file_path)}", "user")
        loading = chat.show_loading("Анализирую файл...")

        # 1. Определение типа файла
        file_type = detect_file_type(file_path)
        if file_type == "unknown":
            chat.add_message(
                "Формат не поддерживается. Загрузите PDF или изображение (PNG, JPG).",
                "bot",
            )
            return

        # 2. Извлечение текста
        text = None

        if file_type == "pdf":
            integrity = check_pdf_integrity(file_path)
            if not integrity["ok"]:
                chat.add_message(f"Ошибка: {integrity['detail']}", "bot")
                return

            result = extract_text_from_pdf(file_path)
            if result["ok"]:
                text = result["text"]
            elif result.get("error_type") == 3:
                # PDF — скан, пробуем OCR
                ocr_result = ocr_image(file_path)
                if not ocr_result["ok"]:
                    chat.add_message(
                        "Не удалось извлечь текст из PDF (скан). OCR тоже не справился.",
                        "bot",
                    )
                    return
                text = postprocess_ocr_text(ocr_result["text"])
            else:
                chat.add_message(
                    f"Не удалось извлечь текст из PDF: {result.get('detail', 'неизвестная ошибка')}",
                    "bot",
                )
                return

        elif file_type in ("png", "jpeg"):
            validation = validate_image(file_path)
            if not validation["ok"]:
                chat.add_message(
                    f"Ошибка валидации изображения: {validation.get('detail', 'неизвестная ошибка')}",
                    "bot",
                )
                return

            ocr_result = ocr_image(file_path)
            if not ocr_result["ok"]:
                chat.add_message(
                    f"Ошибка OCR: {ocr_result.get('detail', 'не удалось распознать текст')}",
                    "bot",
                )
                return
            text = postprocess_ocr_text(ocr_result["text"])

        # 3. Поиск баланса
        balance = find_balance(text)
        if balance["ok"]:
            chat.add_message(
                f"Баланс: {balance['amount']:,.2f} {balance['currency']} "
                f"(уверенность: {balance['confidence']})",
                "bot",
            )
        else:
            chat.add_message("Не удалось найти баланс в документе.", "bot")

        # 4. Парсинг транзакций
        tx_result = parse_transactions(text)
        if not tx_result["ok"]:
            chat.add_message("Не удалось распознать транзакции.", "bot")
            return
        chat.add_message(f"Найдено операций: {tx_result['count']}", "bot")

        # 5. Классификация + агрегация
        classified = classify_transactions(tx_result["transactions"])
        aggregated = aggregate_expenses(classified)
        limited = limit_categories(aggregated["categories"], MAX_CHART_CATEGORIES)

        # 6. Круговая диаграмма
        chart = generate_pie_chart(limited)
        if chart["ok"]:
            chat.add_image(chart["path"], "Расходы по категориям")

        # 7. Сохранение в БД
        period = extract_period(text)
        if period is None:
            period = datetime.now().strftime("%Y-%m")

        save_data = {
            "period_key": period,
            "file_name": os.path.basename(file_path),
            "total_balance": balance["amount"] if balance["ok"] else None,
            "total_income": aggregated["total_income"],
            "total_expense": aggregated["total_expense"],
            "categories": limited,
            "is_reliable": extract_period(text) is not None,
        }

        save_result = save_statement(db_conn, save_data)
        if save_result.get("action") == "duplicate":
            chat.add_message(f"Данные за {period} уже есть. Выполняю замену...", "bot")
            replace_statement(db_conn, save_data)

        # 8. Тренды
        history = get_history(db_conn, HISTORY_MONTHS)
        if history["ok"] and len(history["records"]) >= 2:
            trends = analyze_trends(history["records"])
            if trends["ok"]:
                comment = generate_trend_comment(trends)
                chat.add_message(comment, "bot")

                line = generate_line_chart(history["records"])
                if line["ok"]:
                    chat.add_image(line["path"], "Динамика расходов")

        chat.add_message("Анализ завершён!", "bot")

    except Exception as e:
        chat.add_message(f"Произошла ошибка: {str(e)}", "bot")

    finally:
        if loading is not None:
            chat.hide_loading(loading)


def main():
    root = tk.Tk()
    db_conn = init_db(DB_PATH)

    chat = ChatWindow(
        root,
        on_file_received=lambda path: threading.Thread(
            target=process_file, args=(path, chat, db_conn), daemon=True
        ).start(),
    )

    chat.add_message(
        "Привет! Я финансовый ассистент. "
        "Перетащите банковскую выписку (PDF или скриншот) в это окно.",
        "bot",
    )

    root.mainloop()
    db_conn.close()


if __name__ == "__main__":
    main()
