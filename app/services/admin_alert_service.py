from __future__ import annotations

from datetime import datetime, timedelta

from aiogram import Bot

from app.config import Settings

_last_alert_at: dict[str, datetime] = {}


async def notify_admins(bot: Bot | None, settings: Settings, key: str, text: str, *, throttle_minutes: int = 60) -> None:
    if bot is None or not settings.admin_id_set:
        return
    now = datetime.now()
    last = _last_alert_at.get(key)
    if last and now - last < timedelta(minutes=throttle_minutes):
        return
    _last_alert_at[key] = now
    for admin_id in settings.admin_id_set:
        try:
            await bot.send_message(admin_id, text)
        except Exception:
            continue


def openai_problem_key(exc: Exception | str) -> str | None:
    text = str(exc).lower()
    if "insufficient_quota" in text or "exceeded your current quota" in text or "quota" in text:
        return "openai_quota"
    if "invalid_api_key" in text or "incorrect api key" in text or "401" in text or "authentication" in text:
        return "openai_auth"
    if "billing" in text or "payment" in text:
        return "openai_billing"
    return None


def openai_alert_text(reason: str, model: str | None = None) -> str:
    model_line = f"\nModel: <b>{model}</b>" if model else ""
    return (
        "🚨 <b>Iron Trade OpenAI ogohlantirish</b>\n\n"
        f"Sabab: <b>{reason}</b>{model_line}\n\n"
        "Iron AI fallback rejimda ishlashi mumkin, lekin sifat pasayadi. "
        ".env ichidagi OPENAI_API_KEY, billing va quota holatini tekshiring."
    )
