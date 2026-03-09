LIGHT_THEME = {
    "bg": "#FFFFFF",
    "chat_bg": "#F5F5F5",
    "user_msg_bg": "#DCF8C6",
    "bot_msg_bg": "#FFFFFF",
    "text_color": "#000000",
    "input_bg": "#FFFFFF",
    "input_border": "#CCCCCC",
    "button_bg": "#4CAF50",
    "button_fg": "#FFFFFF",
    "timestamp_color": "#999999",
}

DARK_THEME = {
    "bg": "#1E1E1E",
    "chat_bg": "#2D2D2D",
    "user_msg_bg": "#005C4B",
    "bot_msg_bg": "#383838",
    "text_color": "#FFFFFF",
    "input_bg": "#383838",
    "input_border": "#555555",
    "button_bg": "#4CAF50",
    "button_fg": "#FFFFFF",
    "timestamp_color": "#888888",
}

_THEMES = {
    "light": LIGHT_THEME,
    "dark": DARK_THEME,
}


def get_theme(name: str = "light") -> dict:
    return _THEMES.get(name, LIGHT_THEME)
