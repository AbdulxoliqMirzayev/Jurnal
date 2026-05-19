from __future__ import annotations

def money(value: float | int | None) -> str:
    return "—" if value is None else f"${float(value):,.2f}".replace(",", " ")


def signed_money(value: float | int | None) -> str:
    if value is None:
        return "—"
    number = float(value)
    return f"{number:+,.2f}$".replace(",", " ")
