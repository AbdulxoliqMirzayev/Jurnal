from __future__ import annotations

from app.utils.formatters import money


def risk_amount(deposit: float, risk_percent: float) -> float:
    return float(deposit or 0) * float(risk_percent or 0) / 100


def risk_calculator_message(deposit: float, risk_percent: float) -> str:
    amount = risk_amount(deposit, risk_percent)
    return (
        "🧮 <b>Risk kalkulyator</b>\n\n"
        f"💼 Deposit: <b>{money(deposit)}</b>\n"
        f"⚖️ Risk: <b>{risk_percent:g}%</b>\n"
        f"💵 1 ta savdoda maksimal risk: <b>{money(amount)}</b>\n\n"
        "Agar ketma-ket zarar bo‘lsa:\n"
        f"1 zarar: <b>-{money(amount)}</b>\n"
        f"2 zarar: <b>-{money(amount * 2)}</b>\n"
        f"3 zarar: <b>-{money(amount * 3)}</b>\n"
        f"5 zarar: <b>-{money(amount * 5)}</b>\n\n"
        "Eslatma:\nDo‘stim, tradingda asosiy maqsad tez boyish emas, depositni saqlab qolish."
    )
