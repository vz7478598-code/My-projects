def aggregate_expenses(transactions: list) -> dict:
    categories = {}
    total_expense = 0.0
    total_income = 0.0
    transaction_count = len(transactions)

    for t in transactions:
        amount = t["amount"]
        tx_type = t["type"]

        if tx_type == "expense":
            total_expense += amount
            cat = t["category"]
            categories[cat] = categories.get(cat, 0.0) + amount
        elif tx_type == "income":
            total_income += amount

    categories = {k: round(v, 2) for k, v in categories.items()}

    return {
        "categories": categories,
        "total_expense": round(total_expense, 2),
        "total_income": round(total_income, 2),
        "transaction_count": transaction_count,
    }


def limit_categories(categories: dict, max_categories: int = 7) -> dict:
    if len(categories) <= max_categories:
        return dict(categories)

    sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
    top = sorted_cats[: max_categories - 1]
    rest = sorted_cats[max_categories - 1 :]

    result = dict(top)
    result["Другое"] = round(sum(v for _, v in rest), 2)
    return result
