import re

from utils.number_parser import parse_amount
from utils.date_parser import parse_date

TRANSACTION_PATTERN = re.compile(
    r'(\d{1,2}[./]\d{1,2}[./]\d{2,4})\s+(.+?)\s+([+\-−]?[\d\s]+[.,]\d{2})'
)

EXPENSE_KEYWORDS = ["Покупка", "Оплата", "Списание"]
INCOME_KEYWORDS = ["Пополнение", "Зачисление", "Возврат"]


def parse_transactions(text: str) -> dict:
    transactions = []

    for line in text.splitlines():
        match = TRANSACTION_PATTERN.search(line)
        if not match:
            continue

        date_str = match.group(1)
        description = re.sub(r'\s+', ' ', match.group(2).strip())
        amount_str = match.group(3)

        tx_type = _determine_type(amount_str, line)
        date = parse_date(date_str)
        amount = abs(parse_amount(amount_str))

        transactions.append({
            "date": date,
            "description": description,
            "amount": amount,
            "type": tx_type,
            "raw_line": line.strip(),
        })

    if not transactions:
        return {
            "ok": False,
            "error_type": "no_transactions",
            "detail": "Не удалось найти транзакции в тексте",
        }

    return {
        "ok": True,
        "transactions": transactions,
        "count": len(transactions),
    }


def _determine_type(amount_str: str, line: str) -> str:
    stripped = amount_str.strip()
    if stripped.startswith('-') or stripped.startswith('\u2212'):
        return "expense"
    if stripped.startswith('+'):
        return "income"

    for kw in EXPENSE_KEYWORDS:
        if kw in line:
            return "expense"
    for kw in INCOME_KEYWORDS:
        if kw in line:
            return "income"

    return "income"
