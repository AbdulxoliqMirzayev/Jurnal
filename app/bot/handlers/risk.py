from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.main_menu import RISK_BUTTONS
from app.bot.keyboards.inline_keyboards import risk_percent_keyboard
from app.bot.keyboards.reply_keyboards import main_menu
from app.bot.states.iron_states import RiskStates
from app.database.models import User
from app.database.repositories.deposit_repo import DepositRepository
from app.services.risk_service import risk_calculator_message
from app.utils.menu_lifecycle import clean_answer, clean_callback_answer
from app.utils.validators import parse_positive_float

router = Router(name="risk")


@router.message(F.text.in_(RISK_BUTTONS))
async def risk_section(message: Message) -> None:
    await clean_answer(message, "🧮 <b>Risk kalkulyator</b>\n\nRisk foizini tanlang:", risk_percent_keyboard())


@router.callback_query(F.data.startswith("risk_calc:"))
async def risk_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    value = callback.data.split(":", 1)[1]
    if value == "custom":
        await state.set_state(RiskStates.waiting_custom_percent)
        await clean_callback_answer(callback, "Custom risk foizini yozing. Masalan: 2.5")
        return
    await _send_risk_callback(callback, session, db_user, float(value))


@router.message(RiskStates.waiting_custom_percent)
async def risk_custom(message: Message, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    risk = parse_positive_float(message.text)
    if risk is None or risk > 100:
        await message.answer("Risk foizini to‘g‘ri kiriting. Masalan: 2.5")
        return
    await state.clear()
    await _send_risk(message, session, db_user, risk)


async def _send_risk(message: Message, session: AsyncSession, db_user: User, risk: float) -> None:
    deposit = await DepositRepository(session).current_balance(db_user)
    await clean_answer(message, risk_calculator_message(deposit, risk), main_menu(db_user.language))


async def _send_risk_callback(callback: CallbackQuery, session: AsyncSession, db_user: User, risk: float) -> None:
    deposit = await DepositRepository(session).current_balance(db_user)
    await clean_callback_answer(callback, risk_calculator_message(deposit, risk), main_menu(db_user.language))
