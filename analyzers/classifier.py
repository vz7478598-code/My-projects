CATEGORY_KEYWORDS = {
    "Продукты": ["пятерочка", "магнит", "перекресток", "ашан", "лента", "дикси", "вкусвилл", "продукты", "супермаркет", "гипермаркет", "metro", "spar"],
    "Транспорт": ["яндекс.такси", "uber", "такси", "метро", "автобус", "ржд", "аэрофлот", "бензин", "азс", "лукойл", "газпромнефть", "каршеринг"],
    "Кафе и рестораны": ["кафе", "ресторан", "бар", "макдоналдс", "kfc", "бургер", "пицца", "суши", "coffee", "старбакс", "шоколадница"],
    "ЖКХ и связь": ["жкх", "коммунальн", "электричество", "водоканал", "мтс", "билайн", "мегафон", "теле2", "ростелеком", "интернет", "связь"],
    "Здоровье": ["аптека", "озерки", "ригла", "клиника", "стоматолог", "медицин", "здоровье", "лаборатори", "pharmacy"],
    "Переводы": ["перевод", "transfer", "p2p", "сбп"],
    "Одежда": ["zara", "h&m", "uniqlo", "одежда", "обувь", "спортмастер", "wildberries", "ozon", "lamoda"],
    "Развлечения": ["кино", "театр", "netflix", "spotify", "подписка", "игр", "steam", "playstation"],
}


def classify_transactions(transactions: list) -> list:
    for transaction in transactions:
        description_lower = transaction.get("description", "").lower()
        category = "Другое"
        for cat_name, keywords in CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in description_lower:
                    category = cat_name
                    break
            if category != "Другое":
                break
        transaction["category"] = category
    return transactions
