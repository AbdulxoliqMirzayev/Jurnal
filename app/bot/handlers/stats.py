from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.main_menu import RATING_BUTTONS, STATS_BUTTONS
from app.bot.keyboards.inline_keyboards import period_keyboard, stats_keyboard
from app.bot.keyboards.reply_keyboards import main_menu
from app.database.models import User
from app.services.emotion_service import EmotionService
from app.services.instrument_rating_service import InstrumentRatingService
from app.services.stats_service import StatsService, stats_message
from app.utils.dates import parse_period_days
from app.utils.menu_lifecycle import clean_answer, clean_callback_answer

router = Router(name="stats")


@router.message(F.text.in_(STATS_BUTTONS))
async def stats_section(message: Message) -> None:
    await clean_answer(message, "📊 <b>Statistika</b>\n\nQaysi kesimda ko‘ramiz?", stats_keyboard())


@router.message(F.text.in_(RATING_BUTTONS))
async def rating_section(message: Message) -> None:
    await clean_answer(message, "📈 <b>Instrument reytingi</b>\n\nDavrni tanlang:", period_keyboard("rating"))


@router.callback_query(F.data.startswith("stats:"))
async def stats_callback(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    key = callback.data.split(":", 1)[1]
    if key == "instrument":
        text = await InstrumentRatingService(session).message(db_user, 30, "1 oy")
    elif key == "emotion":
        text = await EmotionService(session).analysis(db_user)
    elif key == "session":
        rows = await StatsService(session).breakdown(db_user, "session", 30)
        text = _breakdown_message("⏱ Session bo‘yicha statistika", rows)
    else:
        labels = {"today": "Bugungi", "week": "Haftalik", "month": "Oylik", "all": "Umumiy"}
        days = parse_period_days(key)
        text = stats_message(await StatsService(session).calculate(db_user, days, labels.get(key, "Statistika")))
    await clean_callback_answer(callback, text, main_menu(db_user.language))


@router.callback_query(F.data.startswith("rating:"))
async def rating_callback(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    period = callback.data.split(":", 1)[1]
    labels = {"week": "1 hafta", "month": "1 oy", "3m": "3 oy", "6m": "6 oy", "all": "Barcha vaqt"}
    text = await InstrumentRatingService(session).message(db_user, parse_period_days(period), labels.get(period, "Davr"))
    await clean_callback_answer(callback, text, main_menu(db_user.language))


def _breakdown_message(title: str, rows: list[tuple[str, int, float]]) -> str:
    if not rows:
        return f"{title}\n\nHali ma’lumot yo‘q, do‘stim."
    lines = [f"{title}\n"]
    for name, trades, net in rows[:10]:
        lines.append(f"\n{name}: {trades} trade, net {net:+.2f}$")
    return "".join(lines)
