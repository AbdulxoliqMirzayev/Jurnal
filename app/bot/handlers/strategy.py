from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.main_menu import STRATEGY_BUTTONS
from app.bot.keyboards.inline_keyboards import strategy_keyboard
from app.bot.keyboards.reply_keyboards import main_menu
from app.database.models import User
from app.services.stats_service import StatsService, strategy_analysis_message
from app.utils.dates import parse_period_days
from app.utils.menu_lifecycle import clean_answer, clean_callback_answer

router = Router(name="strategy")


@router.message(F.text.in_(STRATEGY_BUTTONS))
async def strategy_section(message: Message, language: str | None = None) -> None:
    await clean_answer(
        message,
        "🧠 <b>Strategiya tahlili</b>\n\nQaysi davr bo‘yicha tahlil qilamiz?",
        reply_markup=strategy_keyboard(),
    )


@router.callback_query(F.data.startswith("strategy:"))
async def strategy_period(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    period = callback.data.split(":", 1)[1]
    if period == "ask":
        await clean_callback_answer(
            callback,
            "💬 Strategiyangiz bo‘yicha savolingizni oddiy text qilib yozing. Iron AI jurnal konteksti bilan javob beradi.",
            reply_markup=main_menu(db_user.language),
        )
        return
    if period == "custom":
        await clean_callback_answer(callback, "🔍 Sana oralig‘i keyingi bosqichda kengaytiriladi. Hozircha davr tugmalaridan foydalaning.", strategy_keyboard())
        return
    labels = {"week": "1 hafta", "month": "1 oy", "3m": "3 oy", "6m": "6 oy", "all": "Barcha vaqt"}
    days = parse_period_days(period)
    text = await strategy_analysis_message(StatsService(session), db_user, days, labels.get(period, "Davr"))
    await clean_callback_answer(callback, text, main_menu(db_user.language))
