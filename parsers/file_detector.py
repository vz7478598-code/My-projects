"""Определение типа файла по магическим байтам (сигнатуре)."""

SIGNATURES = {
    b'%PDF':              "pdf",
    b'\x89PNG\r\n\x1a\n': "png",
    b'\xff\xd8\xff':      "jpeg",
}


def detect_file_type(file_path: str) -> str:
    """
    Определяет тип файла по магическим байтам (первые 8 байт).

    Возвращает: "pdf", "png", "jpeg" или "unknown".
    """
    with open(file_path, 'rb') as f:
        header = f.read(8)

    for sig, file_type in SIGNATURES.items():
        if header.startswith(sig):
            return file_type

    return "unknown"
