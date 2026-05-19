from __future__ import annotations

TRADING_DAYS = {
    "3_days": 3,
    "1_week": 5,
    "1_month": 20,
    "3_months": 60,
    "100_days": 100,
    "6_months": 120,
    "1_year": 240,
    "5_years": 1200,
}

PERIOD_LABELS_UZ = {
    "3_days": "3 trading kunda",
    "1_week": "1 haftada",
    "1_month": "1 oyda",
    "3_months": "3 oyda",
    "100_days": "100 trading kunda",
    "6_months": "6 oyda",
    "1_year": "1 yilda",
    "5_years": "5 yilda",
}


def calculate_compound_projection(balance: float, daily_percent: float) -> dict[str, float]:
    result: dict[str, float] = {}
    for period, days in TRADING_DAYS.items():
        result[period] = calculate_compound_amount(balance, daily_percent, days)
    return result


def calculate_compound_amount(balance: float, daily_percent: float, trading_days: int) -> float:
    return float(balance) * ((1 + float(daily_percent) / 100) ** int(trading_days))


def calculate_compound_projection_for_days(
    balance: float,
    daily_percent: float,
    trading_days: tuple[int, ...] = (3, 60, 100, 240),
) -> dict[int, float]:
    return {days: calculate_compound_amount(balance, daily_percent, days) for days in trading_days}


def money_text(value: float | int | None) -> str:
    if value is None:
        return "-"
    return f"{float(value):,.2f}$"


def signed_money_text(value: float | int | None) -> str:
    if value is None:
        return "-"
    return f"{float(value):+,.2f}$"


def percent_text(value: float | int | None) -> str:
    if value is None:
        return "-"
    return f"{float(value):.2f}%"


def format_compound_projection(balance: float, daily_percent: float) -> str:
    projection = calculate_compound_projection(balance, daily_percent)
    lines = [
        "📊 <b>Matematik taxmin</b>",
        "",
        f"Sizning balansingiz: <b>{money_text(balance)}</b>",
        f"Tanlangan kunlik risk/maqsad: <b>{daily_percent:g}%</b>",
        "",
        f"Agar siz har trading kuni o'rtacha {daily_percent:g}% natija qilsangiz:",
        "",
    ]
    for period, amount in projection.items():
        lines.append(f"{PERIOD_LABELS_UZ[period]}: <b>{money_text(amount)}</b>")
    lines.extend(
        [
            "",
            "⚠️ Eslatma: Forex bozori odatda haftasiga 5 kun ochiq bo'ladi. "
            "Bu hisob-kitob calendar kunlar bo'yicha emas, trading kunlar bo'yicha qilindi. "
            "Bu kafolatlangan foyda emas, faqat matematik taxmin.",
        ]
    )
    return "\n".join(lines)


def format_projection_message(balance: float, daily_percent: float, lang: str = "uz") -> str:
    return format_compound_projection(balance, daily_percent)


def calculate_risk_amount(balance: float, risk_percent: float) -> float:
    return round(balance * risk_percent / 100, 2)


def calculate_result_percent(net_result: float, balance: float) -> float:
    if balance <= 0:
        return 0.0
    return round(net_result / balance * 100, 2)
