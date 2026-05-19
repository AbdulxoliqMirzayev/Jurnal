from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.main_menu import ALL_MENU_BUTTONS
from app.bot.keyboards.admin_keyboards import admin_keyboard
from app.bot.keyboards.reply_keyboards import main_menu
from app.config import Settings
from app.database.models import User
from app.services.ai_service import IronAIService
from app.services.stats_service import StatsService
from app.utils.menu_lifecycle import clean_answer

router = Router(name="ai_chat")


@router.message(F.text)
async def iron_ai_chat(
    message: Message,
    session: AsyncSession,
    db_user: User,
    settings: Settings,
    language: str | None = None,
) -> None:
    text = (message.text or "").strip()
    if not text or text.startswith("/") or text in ALL_MENU_BUTTONS:
        return
    if settings.is_admin_user(message.from_user.id, message.from_user.username):
        await clean_answer(message, "🛡 <b>Admin panel</b>", admin_keyboard())
        return
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    context = None
    if _needs_journal_context(text):
        context = await StatsService(session).ai_context(db_user, 30)
    reply = await IronAIService(settings, message.bot).reply(text, language or db_user.language or "uz", context)
    await message.answer(reply, reply_markup=main_menu(language or db_user.language))


def _needs_journal_context(text: str) -> bool:
    lower = text.lower()
    keywords = (
        "natijam",
        "statistika",
        "qaysi",
        "zarar",
        "foyda",
        "overtrading",
        "riskim",
        "sessiya",
        "instrument",
        "xauusd",
        "btc",
        "emotion",
    )
    return any(word in lower for word in keywords)
