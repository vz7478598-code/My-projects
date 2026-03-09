"""Post-processing module for cleaning raw OCR text output."""

import re

# Digit-like chars: real digits + Cyrillic/Latin OCR lookalikes
_DL = r'[0-9ОоЗбlISB]'
# Date-specific digit-like (subset)
_DD = r'[0-9ОоЗ]'

# Amount: optional minus (incl. Unicode minus sign), digit-likes with spaces, decimal, 2 digit-likes
_RE_AMOUNT = re.compile(rf'[-\u2212]?{_DL}(?:{_DL}|\s)*[.,]{_DL}{{2}}')

# Date: DD.MM.YYYY / DD/MM/YYYY / DD-MM-YYYY
_RE_DATE = re.compile(rf'{_DD}{{1,2}}[./-]{_DD}{{1,2}}[./-][0-9]{{2,4}}')

_AMOUNT_CHAR_MAP = {
    'О': '0', 'о': '0',
    'З': '3',
    'б': '6',
    'l': '1',
    'I': '1',
    'S': '5',
    'B': '8',
    '\u2212': '-',  # Unicode minus sign → hyphen-minus
}

_DATE_CHAR_MAP = {
    'О': '0', 'о': '0',
    'З': '3',
}


def _fix_chars(match: re.Match, char_map: dict[str, str]) -> str:
    result = match.group(0)
    for wrong, correct in char_map.items():
        result = result.replace(wrong, correct)
    return result


def postprocess_ocr_text(raw_text: str) -> str:
    """Clean raw OCR text: normalize whitespace and fix common OCR errors in amounts/dates."""
    text = raw_text

    # 1. Collapse multiple spaces/tabs (preserve newlines)
    text = re.sub(r'[ \t]+', ' ', text)

    # 2. Collapse 3+ consecutive newlines to 2
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 3. Fix OCR errors in amounts
    text = _RE_AMOUNT.sub(lambda m: _fix_chars(m, _AMOUNT_CHAR_MAP), text)

    # 4. Fix OCR errors in dates
    text = _RE_DATE.sub(lambda m: _fix_chars(m, _DATE_CHAR_MAP), text)

    return text.strip()
