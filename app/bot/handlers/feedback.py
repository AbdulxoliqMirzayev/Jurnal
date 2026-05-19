from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.main_menu import FEEDBACK_BUTTONS
from app.bot.keyboards.inline_keyboards import admin_contact_keyboard
from app.bot.keyboards.reply_keyboards import main_menu
from app.bot.states.iron_states import FeedbackStates
from app.config import Settings
from app.database.models import User
from app.database.repositories.feedback_repo import FeedbackRepository
from app.utils.menu_lifecycle import clean_answer

router = Router(name="feedback")


@router.message(F.text.in_(FEEDBACK_BUTTONS))
async def feedback_section(message: Message, state: FSMContext, settings: Settings) -> None:
    await state.set_state(FeedbackStates.waiting_feedback)
    await clean_answer(
        message,
        "💬 Taklif, savol yoki murojaatingiz bo‘lsa, admin bilan bog‘lanishingiz mumkin.\n\n"
        f"Admin: <b>@{settings.resolved_admin_username}</b>\n\n"
        "Yoki shu yerga murojaatingizni yozib yuboring.",
        reply_markup=admin_contact_keyboard(settings.resolved_admin_username),
    )


@router.message(FeedbackStates.waiting_feedback)
async def save_feedback(message: Message, state: FSMContext, session: AsyncSession, db_user: User, settings: Settings) -> None:
    text = (message.text or "").strip()
    if len(text) < 3:
        await message.answer("Murojaat matnini yozing, do‘stim.")
        return
    feedback = await FeedbackRepository(session).create(db_user, text)
    for admin_id in settings.admin_id_set:
        try:
            await message.bot.send_message(
                admin_id,
                "💬 <b>Yangi murojaat</b>\n\n"
                f"User: @{db_user.username or '-'} / {db_user.telegram_id}\n"
                f"ID: {feedback.id}\n\n{text}",
            )
        except Exception:
            continue
    await state.clear()
    await clean_answer(message, "✅ Murojaatingiz saqlandi va adminga yuborildi.", main_menu(db_user.language))
