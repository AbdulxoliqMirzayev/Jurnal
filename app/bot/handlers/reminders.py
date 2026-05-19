from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.main_menu import REMINDER_BUTTONS
from app.bot.keyboards.inline_keyboards import reminder_keyboard
from app.bot.keyboards.reply_keyboards import main_menu
from app.bot.states.iron_states import JournalStates, ReminderStates
from app.config import Settings
from app.database.models import User
from app.database.repositories.reminder_repo import ReminderRepository
from app.services.reminder_service import default_reminder_time
from app.utils.dates import parse_hhmm
from app.utils.menu_lifecycle import clean_answer, clean_callback_answer
from app.utils.stickers import safe_send_sticker

router = Router(name="reminders")


@router.message(F.text.in_(REMINDER_BUTTONS))
async def reminder_section(message: Message, settings: Settings) -> None:
    await safe_send_sticker(message.bot, message.chat.id, "reminder", settings)
    await clean_answer(message, "⏰ Kunlik jurnal eslatmasini yoqmoqchimisiz?", reminder_keyboard())


@router.callback_query(F.data.startswith("reminder:"))
async def reminder_action(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User, settings: Settings) -> None:
    action = callback.data.split(":", 1)[1]
    repo = ReminderRepository(session)
    if action == "on":
        reminder = await repo.set_enabled(db_user, True, default_reminder_time(settings), settings.default_timezone)
        await clean_callback_answer(
            callback,
            f"✅ Eslatma yoqildi: <b>{reminder.reminder_time.strftime('%H:%M')}</b> ({reminder.timezone})",
            reply_markup=main_menu(db_user.language),
        )
    elif action == "off":
        await repo.set_enabled(db_user, False, default_reminder_time(settings), settings.default_timezone)
        await clean_callback_answer(callback, "❌ Eslatma o‘chirildi.", main_menu(db_user.language))
    elif action == "time":
        await state.set_state(ReminderStates.waiting_time)
        await clean_callback_answer(callback, "Qaysi vaqtda eslatma yuboray? Masalan: 21:30")
    elif action == "journal":
        await state.set_state(JournalStates.waiting_text)
        from app.bot.handlers.journal import JOURNAL_PROMPT

        await clean_callback_answer(callback, JOURNAL_PROMPT, main_menu(db_user.language))


@router.message(ReminderStates.waiting_time)
async def reminder_time(message: Message, state: FSMContext, session: AsyncSession, db_user: User, settings: Settings) -> None:
    value = parse_hhmm(message.text or "")
    if value is None:
        await message.answer("Vaqtni HH:MM formatida yozing. Masalan: 21:30")
        return
    await ReminderRepository(session).set_time(db_user, value, settings.default_timezone)
    await state.clear()
    await clean_answer(message, f"✅ Eslatma vaqti saqlandi: <b>{value.strftime('%H:%M')}</b>", main_menu(db_user.language))
