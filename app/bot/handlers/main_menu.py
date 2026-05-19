from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.admin_keyboards import admin_keyboard
from app.bot.keyboards.reply_keyboards import BTN_AI_HELP, main_menu
from app.config import Settings
from app.utils.menu_lifecycle import clean_answer, clean_callback_answer

router = Router(name="main_menu")


@router.callback_query(F.data == "menu:main")
async def show_main_menu(callback: CallbackQuery, state: FSMContext, settings: Settings, language: str | None = None) -> None:
    await state.clear()
    if settings.is_admin_user(callback.from_user.id, callback.from_user.username):
        await clean_callback_answer(callback, "🛡 <b>Admin panel</b>", admin_keyboard())
        return
    await clean_callback_answer(callback, "🏠 Asosiy menyu", main_menu(language))


@router.message(F.text == BTN_AI_HELP)
async def ai_help(message: Message, language: str | None = None) -> None:
    await clean_answer(
        message,
        "🤖 <b>Iron AI yordam</b>\n\n"
        "Do‘stim, trading jurnal, risk, strategiya, emotion yoki statistika bo‘yicha savolingizni oddiy text qilib yozing.\n\n"
        "Masalan:\n"
        "• Nega men zarar qilyapman?\n"
        "• Men overtrading qilyapmanmi?\n"
        "• XAUUSD bo‘yicha natijam qanday?\n\n"
        "Men aniq buy/sell signal bermayman, faqat jurnal va ta’limiy tahlil qilaman.",
        reply_markup=main_menu(language),
    )
