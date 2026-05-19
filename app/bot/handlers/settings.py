from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.main_menu import SETTINGS_BUTTONS
from app.bot.keyboards.inline_keyboards import language_keyboard, risk_type_keyboard, settings_keyboard
from app.bot.keyboards.reply_keyboards import main_menu, trading_type_keyboard
from app.bot.states.iron_states import SettingsStates
from app.config import Settings
from app.database.models import DepositTransaction, Reminder, StrategyProfile, TradeJournal, TradeScreenshot, User, UserProfile
from app.database.repositories.deposit_repo import DepositRepository
from app.database.repositories.reminder_repo import ReminderRepository
from app.database.repositories.user_repo import UserRepository
from app.services.ai_service import IronAIService
from app.utils.dates import parse_hhmm
from app.utils.formatters import money
from app.utils.menu_lifecycle import clean_answer, clean_callback_answer
from app.utils.validators import parse_positive_float

router = Router(name="settings")


@router.message(F.text.in_(SETTINGS_BUTTONS))
async def settings_section(message: Message) -> None:
    await clean_answer(message, "⚙️ <b>Sozlamalar</b>\n\nQaysi sozlamani o‘zgartiramiz?", settings_keyboard())


@router.callback_query(F.data.startswith("settings:"))
async def settings_action(callback: CallbackQuery, state: FSMContext) -> None:
    action = callback.data.split(":", 1)[1]
    if action == "language":
        await clean_callback_answer(callback, "🌐 Tilni tanlang:", language_keyboard("settings_lang"))
    elif action == "trading_type":
        await state.update_data(settings_action=action)
        await state.set_state(SettingsStates.waiting_value)
        await clean_callback_answer(callback, "📊 Trading turini tanlang:", trading_type_keyboard())
    elif action in {"deposit_set", "deposit_add", "deposit_withdraw", "strategy", "reminder_time"}:
        await state.update_data(settings_action=action)
        await state.set_state(SettingsStates.waiting_value)
        prompts = {
            "deposit_set": "Yangi deposit balansini yozing. Masalan: 1000$",
            "deposit_add": "Qancha deposit qo‘shildi? Masalan: 200$",
            "deposit_withdraw": "Qancha deposit yechildi? Masalan: 100$",
            "strategy": "Yangi strategiyangizni yozing.",
            "reminder_time": "Yangi eslatma vaqtini yozing. Masalan: 21:30",
        }
        await clean_callback_answer(callback, prompts[action])
    elif action == "risk":
        await clean_callback_answer(callback, "⚖️ Risk turini tanlang:", risk_type_keyboard("settings_risk"))
    elif action == "clear_confirm":
        await clean_callback_answer(callback, "🗑 Ma’lumotlarni tozalash xavfli. Tasdiqlash uchun: TOZALASH deb yozing.")
        await state.update_data(settings_action=action)
        await state.set_state(SettingsStates.waiting_value)


@router.callback_query(F.data.startswith("settings_lang:"))
async def settings_language(callback: CallbackQuery, session: AsyncSession, db_user: User, settings: Settings) -> None:
    language = callback.data.split(":", 1)[1]
    await UserRepository(session, settings).set_language(db_user, language)
    await clean_callback_answer(callback, "✅ Til saqlandi.", main_menu(language))


@router.callback_query(F.data.startswith("settings_risk:"))
async def settings_risk(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    risk_type = callback.data.split(":", 1)[1]
    mapping = {"conservative": 1.0, "normal": 3.0, "aggressive": 5.0}
    if risk_type == "custom":
        await state.update_data(settings_action="risk_custom")
        await state.set_state(SettingsStates.waiting_value)
        await clean_callback_answer(callback, "Custom risk foizini kiriting. Masalan: 2.5")
        return
    await DepositRepository(session).set_risk(db_user, risk_type, mapping[risk_type])
    await clean_callback_answer(callback, f"✅ Risk saqlandi: <b>{risk_type}</b>", main_menu(db_user.language))


@router.message(SettingsStates.waiting_value)
async def settings_value(message: Message, state: FSMContext, session: AsyncSession, db_user: User, settings: Settings) -> None:
    data = await state.get_data()
    action = data.get("settings_action")
    text = (message.text or "").strip()
    repo = DepositRepository(session)
    if action == "trading_type":
        lower = text.lower()
        if "forex" not in lower and "crypto" not in lower:
            await message.answer("Iltimos, 💱 Forex yoki 🪙 Crypto tanlang.", reply_markup=trading_type_keyboard())
            return
        await UserRepository(session, settings).set_trading_type(db_user, "crypto" if "crypto" in lower else "forex")
        response = "✅ Trading turi saqlandi."
    elif action in {"deposit_set", "deposit_add", "deposit_withdraw"}:
        amount = parse_positive_float(text)
        if amount is None:
            await message.answer("Musbat son kiriting. Masalan: 500$")
            return
        if action == "deposit_set":
            profile = await repo.get_profile(db_user)
            profile.deposit_current = amount
            response = f"✅ Deposit yangilandi: <b>{money(amount)}</b>"
        elif action == "deposit_add":
            await repo.add(db_user, amount, "settings add")
            response = f"✅ Deposit qo‘shildi: <b>{money(amount)}</b>"
        else:
            await repo.withdraw(db_user, amount, "settings withdraw")
            response = f"✅ Deposit yechildi: <b>{money(amount)}</b>"
    elif action == "strategy":
        organized = await IronAIService(settings, message.bot).organize_strategy(text, db_user.trading_type)
        profile = await session.scalar(select(UserProfile).where(UserProfile.user_id == db_user.id))
        if profile:
            profile.strategy_text = organized.get("clean_strategy_text") or text
            profile.trading_style = organized.get("trading_style")
            profile.timeframe = organized.get("timeframe")
            profile.favorite_instruments = organized.get("instruments")
        response = "✅ Strategiya yangilandi."
    elif action == "risk_custom":
        risk = parse_positive_float(text)
        if risk is None or risk > 100:
            await message.answer("Risk foizini to‘g‘ri kiriting. Masalan: 2.5")
            return
        await repo.set_risk(db_user, "custom", risk)
        response = f"✅ Custom risk saqlandi: <b>{risk:g}%</b>"
    elif action == "reminder_time":
        reminder_time = parse_hhmm(text)
        if reminder_time is None:
            await message.answer("Vaqtni HH:MM formatida kiriting. Masalan: 21:30")
            return
        await ReminderRepository(session).set_time(db_user, reminder_time, settings.default_timezone)
        response = f"✅ Eslatma vaqti saqlandi: <b>{reminder_time.strftime('%H:%M')}</b>"
    elif action == "clear_confirm":
        if text != "TOZALASH":
            await clean_answer(message, "Bekor qilindi.", main_menu(db_user.language))
            await state.clear()
            return
        await session.execute(delete(TradeScreenshot).where(TradeScreenshot.user_id == db_user.id))
        await session.execute(delete(TradeJournal).where(TradeJournal.user_id == db_user.id))
        await session.execute(delete(DepositTransaction).where(DepositTransaction.user_id == db_user.id))
        await session.execute(delete(StrategyProfile).where(StrategyProfile.user_id == db_user.id))
        response = "🗑 Jurnal, screenshot, deposit va strategiya ma’lumotlari tozalandi."
    else:
        response = "Sozlama topilmadi."
    await state.clear()
    await clean_answer(message, response, main_menu(db_user.language))
