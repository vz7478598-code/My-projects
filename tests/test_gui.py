from gui.theme import get_theme, LIGHT_THEME, DARK_THEME


def test_theme_light():
    theme = get_theme("light")
    assert "bg" in theme


def test_theme_dark():
    theme = get_theme("dark")
    assert theme["bg"] == "#1E1E1E"


def test_theme_default():
    theme = get_theme()
    assert theme is LIGHT_THEME
