from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.admin_keyboards import admin_keyboard
from app.bot.keyboards.inline_keyboards import language_keyboard, risk_type_keyboard
from app.bot.keyboards.reply_keyboards import main_menu, trading_type_keyboard
from app.bot.states.iron_states import OnboardingStates
from app.config import Settings
from app.database.models import StrategyProfile, User
from app.database.repositories.deposit_repo import DepositRepository
from app.database.repositories.user_repo import UserRepository
from app.services.ai_service import IronAIService
from app.utils.formatters import money
from app.utils.finance_math import calculate_compound_projection_for_days, calculate_risk_amount
from app.utils.menu_lifecycle import clean_answer, clean_callback_answer
from app.utils.message_manager import delete_tracked_messages, track_message
from app.utils.stickers import safe_send_animation, safe_send_sticker
from app.utils.validators import parse_positive_float

router = Router(name="start")


START_TEXT = (
    "👋 Assalomu alaykum, do‘stim!\n\n"
    "Men <b>Iron Trade</b> — sizning shaxsiy <b>AI trading jurnal boshqaruvchingizman</b>.\n\n"
    "🧠 <b>AI trading jurnal nima?</b>\n"
    "Bu oddiy daftar emas. Men har bir trade, risk, emotion, sabab, natija va screenshotni tartiblab, "
    "sizga qayerda xato qilayotganingizni va qayerda kuchli ishlayotganingizni ko‘rsataman.\n\n"
    "Sizga beradigan eng foydali tomonlarim:\n"
    "📘 Savdolaringizni avtomatik jurnalga saqlayman\n"
    "⚖️ Riskni hisoblab, depositni asrashga yordam beraman\n"
    "😐 Shoshilish, qo‘rquv va revenge trade xatolarini topaman\n"
    "📊 Qaysi instrument, sessiya va setup sizga mosligini ko‘rsataman\n"
    "🧠 Strategiyangizni real natijalaringiz asosida tahlil qilaman\n"
    "📄 PDF/Excel hisobot tayyorlab beraman\n\n"
    "Maqsadim signal berish emas. Maqsad — sizni intizomli, riskni tushunadigan va xatosini ko‘ra oladigan traderga aylantirish.\n\n"
    "Boshlaymiz. Tilni tanlang:"
)


@router.message(CommandStart())
async def command_start(message: Message, state: FSMContext, settings: Settings) -> None:
    await state.clear()
    await delete_tracked_messages(message.bot, message.chat.id)
    await safe_send_animation(message.bot, message.chat.id, "welcome", settings)
    await safe_send_sticker(message.bot, message.chat.id, "welcome", settings)
    if settings.is_admin_user(message.from_user.id, message.from_user.username):
        sent = await message.answer(_admin_welcome(settings), reply_markup=admin_keyboard())
        await track_message(message.chat.id, sent.message_id)
        return
    sent = await message.answer(START_TEXT, reply_markup=language_keyboard())
    await track_message(message.chat.id, sent.message_id)


@router.message(Command("menu"))
async def command_menu(message: Message, state: FSMContext, settings: Settings, language: str | None = None) -> None:
    await state.clear()
    if settings.is_admin_user(message.from_user.id, message.from_user.username):
        await clean_answer(message, "🛡 <b>Admin panel</b>", admin_keyboard())
        return
    await clean_answer(message, "🏠 Asosiy menyu", main_menu(language))


@router.callback_query(F.data.startswith("lang:"))
async def set_language(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User, settings: Settings) -> None:
    language = callback.data.split(":", 1)[1]
    if language not in {"uz", "en", "ru"}:
        language = settings.default_language
    await UserRepository(session, settings).set_language(db_user, language)
    await state.set_state(OnboardingStates.waiting_trading_type)
    await clean_callback_answer(callback, "📊 Siz qaysi yo‘nalishda savdo qilasiz?", trading_type_keyboard())


@router.message(OnboardingStates.waiting_trading_type)
async def choose_trading_type(message: Message, state: FSMContext, session: AsyncSession, db_user: User, settings: Settings) -> None:
    text = (message.text or "").lower()
    if "forex" in text:
        trading_type = "forex"
    elif "crypto" in text or "kripto" in text:
        trading_type = "crypto"
    else:
        await clean_answer(message, "Iltimos, 💱 Forex yoki 🪙 Crypto tugmasidan birini tanlang.", trading_type_keyboard())
        return
    await UserRepository(session, settings).set_trading_type(db_user, trading_type)
    await state.update_data(trading_type=trading_type)
    await state.set_state(OnboardingStates.waiting_strategy)
    await clean_answer(message, _strategy_prompt(trading_type))


@router.message(OnboardingStates.waiting_strategy)
async def save_strategy(message: Message, state: FSMContext, session: AsyncSession, db_user: User, settings: Settings) -> None:
    text = (message.text or "").strip()
    if len(text) < 10:
        await message.answer("Do‘stim, strategiyani biroz batafsil yozing. Masalan: instrument, timeframe, entry sababi va risk.")
        return
    data = await state.get_data()
    trading_type = data.get("trading_type") or db_user.trading_type
    organized = await IronAIService(settings, message.bot).organize_strategy(text, trading_type)
    profile = await UserRepository(session, settings).ensure_profile(db_user)
    profile.strategy_text = organized.get("clean_strategy_text") or text
    profile.trading_style = organized.get("trading_style")
    profile.timeframe = organized.get("timeframe")
    profile.favorite_instruments = organized.get("instruments")
    profile.market_type = organized.get("market_type")
    profile.leverage_usage = organized.get("leverage_usage")
    session.add(
        StrategyProfile(
            user_id=db_user.id,
            trading_type=trading_type,
            strategy_text=profile.strategy_text,
            trading_style=profile.trading_style,
            timeframe=profile.timeframe,
            instruments=profile.favorite_instruments,
            risk_preference=organized.get("risk_preference"),
            market_type=profile.market_type,
            leverage_usage=profile.leverage_usage,
        )
    )
    await session.flush()
    await state.set_state(OnboardingStates.waiting_deposit)
    await clean_answer(
        message,
        "✅ Strategiyangiz saqlandi, do‘stim.\n\n"
        "💼 Balansingizda qancha deposit bor?\n\n"
        "Masalan:\n200$\n500$\n1000$"
    )


@router.message(OnboardingStates.waiting_deposit)
async def save_deposit(message: Message, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    amount = parse_positive_float(message.text)
    if amount is None:
        await message.answer("Depositni musbat son ko‘rinishida yuboring. Masalan: 500$")
        return
    await DepositRepository(session).set_initial(db_user, amount)
    await state.set_state(None)
    await clean_answer(
        message,
        f"✅ Deposit saqlandi: <b>{money(amount)}</b>\n\n⚖️ Risk turini tanlang:",
        reply_markup=risk_type_keyboard("onboard_risk"),
    )


@router.callback_query(F.data.startswith("onboard_risk:"))
async def save_risk_type(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    risk_type = callback.data.split(":", 1)[1]
    if risk_type == "custom":
        await state.set_state(OnboardingStates.waiting_custom_risk)
        await clean_callback_answer(callback, "Odatda bitta savdoda depositning nechchi foizini risk qilasiz?")
        return
    mapping = {"conservative": 1.0, "normal": 3.0, "aggressive": 5.0}
    profile = await DepositRepository(session).set_risk(db_user, risk_type, mapping[risk_type])
    await state.clear()
    await clean_callback_answer(
        callback,
        _risk_projection_message(float(profile.deposit_current or 0), mapping[risk_type]),
        reply_markup=main_menu(db_user.language),
    )


@router.message(OnboardingStates.waiting_custom_risk)
async def save_custom_risk(message: Message, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    risk = parse_positive_float(message.text)
    if risk is None or risk > 100:
        await message.answer("Risk foizini to‘g‘ri kiriting. Masalan: 2 yoki 3.5")
        return
    profile = await DepositRepository(session).set_risk(db_user, "custom", risk)
    await state.clear()
    await message.answer(
        _risk_projection_message(float(profile.deposit_current or 0), risk),
        reply_markup=main_menu(db_user.language),
    )


def _admin_welcome(settings: Settings) -> str:
    admin_ids = ", ".join(str(item) for item in sorted(settings.admin_id_set)) or "ID kiritilmagan"
    return (
        "🛡 <b>Iron Trade Admin Panel</b>\n\n"
        "Siz admin sifatida kirdingiz. User onboarding ko‘rsatilmaydi.\n\n"
        f"Admin username: <b>@{settings.resolved_admin_username}</b>\n"
        f"Admin IDs: <b>{admin_ids}</b>\n\n"
        "Quyidagi paneldan bot statistikasi, murojaatlar, broadcast va OpenAI holatini boshqaring."
    )


def _strategy_prompt(trading_type: str) -> str:
    if trading_type == "crypto":
        return (
            "🧠 Do‘stim, crypto savdo usulingizni yozib bering.\n\n"
            "Masalan:\n"
            "🪙 Qaysi coinlarni ko‘proq savdo qilasiz?\n"
            "📈 Spotmi yoki Futures?\n"
            "⚖️ Leverage ishlatasizmi?\n"
            "⏱ Qaysi timeframe’da ishlaysiz?\n"
            "📌 Nimaga asoslanib coin olasiz yoki sotasiz?"
        )
    return (
        "🧠 Do‘stim, menga strategiyangizni yozib tushuntirib bering.\n\n"
        "Masalan:\n"
        "💱 Qaysi paralar bilan ishlaysiz?\n"
        "⏱ Qaysi timeframe’da savdo qilasiz?\n"
        "📌 Nimaga asoslanib savdoga kirasiz?\n"
        "⚖️ Odatda nechchi foiz risk qilasiz?\n"
        "📊 Strategiyangiz SMC, ICT, Price Action, Indicator, News yoki aralash usulmi?\n\n"
        "Bu kelajakda savdolaringizni aniqroq tahlil qilishimga yordam beradi."
    )


def _risk_projection_message(deposit: float, risk_percent: float) -> str:
    risk_amount = calculate_risk_amount(deposit, risk_percent)
    projection = calculate_compound_projection_for_days(deposit, risk_percent)
    return (
        "✅ <b>Risk sozlamalari saqlandi.</b>\n\n"
        "🧮 <b>Sizning risk rejangiz</b>\n"
        f"💼 Deposit: <b>{money(deposit)}</b>\n"
        f"⚖️ Tanlangan risk: <b>{risk_percent:g}%</b>\n"
        f"💵 1 ta savdoda maksimal risk: <b>{money(risk_amount)}</b>\n\n"
        "📈 <b>Matematik compound ssenariy</b>\n"
        f"Agar har trading kuni o‘rtacha <b>+{risk_percent:g}%</b> intizomli natija qilsangiz:\n"
        f"• 3 trading kunda: <b>{money(projection[3])}</b>\n"
        f"• 60 trading kunda: <b>{money(projection[60])}</b>\n"
        f"• 100 trading kunda: <b>{money(projection[100])}</b>\n"
        f"• 1 yildan keyin, taxminan 240 trading kun: <b>{money(projection[240])}</b>\n\n"
        "🧠 <b>Iron AI sizga qanday yordam beradi?</b>\n"
        "Men har savdoni jurnalga tushirib, strategiyangizni, riskni, emotionni va takroriy xatolarni tahlil qilaman. "
        "Maqsad shunchaki ko‘p trade qilish emas — reja bilan kirish, riskni asrash va intizomni kuchaytirish.\n\n"
        "Birgalikda strategiyangizni tahlil qilib, qaysi joyda kuchli va qaysi joyda depositga zarar kelayotganini topamiz.\n\n"
        "⚠️ Bu kafolatlangan foyda emas va moliyaviy maslahat emas. Bu faqat matematik taxmin va trading jurnal intizomi uchun yo‘l xaritasi.\n\n"
        "🏠 <b>Iron Trade asosiy menyusi tayyor.</b>"
    )
