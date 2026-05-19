from __future__ import annotations

import re


class NumberParseError(ValueError):
    pass


def parse_number(value: str, allow_negative: bool = True) -> float:
    raw = (value or "").strip()
    if not raw:
        raise NumberParseError("empty value")
    match = re.search(r"[+-]?\d[\d\s,]*(?:\.\d+)?", raw.replace("\u00a0", " "))
    if not match:
        raise NumberParseError(f"no number in {value!r}")
    token = match.group(0).strip()
    token = token.replace(" ", "")
    if "," in token and "." in token:
        token = token.replace(",", "")
    elif "," in token:
        parts = token.split(",")
        if len(parts[-1]) == 3 and all(part.isdigit() for part in parts):
            token = "".join(parts)
        else:
            token = token.replace(",", ".")
    try:
        number = float(token)
        if number < 0 and not allow_negative:
            raise NumberParseError("negative number is not allowed")
        return number
    except ValueError as exc:
        raise NumberParseError(f"invalid number {value!r}") from exc


def parse_positive_number(value: str) -> float:
    number = parse_number(value)
    if number <= 0:
        raise NumberParseError("number must be positive")
    return number


def parse_non_negative_number(value: str) -> float:
    number = parse_number(value, allow_negative=False)
    if number < 0:
        raise NumberParseError("number must not be negative")
    return number


def parse_lot(value: str) -> float:
    number = parse_positive_number(value)
    if number < 0.001:
        raise NumberParseError("lot is too small")
    return round(number, 3)


def parse_trade_count(value: str) -> int:
    number = parse_positive_number(value)
    count = int(number)
    if count != number or count < 1 or count > 1000:
        raise NumberParseError("trade count must be an integer between 1 and 1000")
    return count


def parse_pnl(value: str) -> float:
    return round(parse_number(value.replace("-", ""), allow_negative=False), 2)


def format_money(amount: float, currency: str = "$") -> str:
    return f"{float(amount):,.2f}{currency}"
