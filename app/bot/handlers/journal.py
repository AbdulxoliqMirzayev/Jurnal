from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.main_menu import JOURNAL_BUTTONS
from app.bot.keyboards.reply_keyboards import emotion_keyboard, main_menu
from app.bot.states.iron_states import JournalStates
from app.config import Settings
from app.database.models import User
from app.database.repositories.journal_repo import JournalRepository
from app.database.repositories.screenshot_repo import ScreenshotRepository
from app.services.emotion_service import EmotionService
from app.services.journal_parser import JournalParser, required_missing_fields
from app.services.vision_service import VisionService
from app.utils.formatters import signed_money
from app.utils.menu_lifecycle import clean_answer
from app.utils.stickers import safe_send_animation, safe_send_sticker

router = Router(name="journal")


JOURNAL_PROMPT = (
    "📘 <b>Bugungi savdolaringizni jurnalga yozamiz, do‘stim.</b>\n\n"
    "Iltimos, quyidagilarni yozib yuboring:\n\n"
    "🔢 Bugun nechta savdo qildingiz?\n"
    "💱 Qaysi para yoki coin?\n"
    "⏱ Qaysi vaqt oralig‘ida?\n"
    "📌 Nimaga asoslanib savdoga kirdingiz?\n"
    "⚖️ Risk foizi qancha bo‘ldi?\n"
    "💰 Qancha foyda yoki zarar qildingiz?\n"
    "😐 Savdo paytidagi holatingiz qanday edi?\n"
    "📸 Savdoga kirishdan oldingi chart screenshotini yuboring.\n"
    "📸 Savdodan keyingi chart screenshotini ham yuboring.\n\n"
    "Text va rasm yuborishingiz mumkin. Men avtomatik tahlil qilib saqlayman."
)


@router.message(F.text.in_(JOURNAL_BUTTONS))
async def start_journal(message: Message, state: FSMContext, settings: Settings, language: str | None = None) -> None:
    await state.clear()
    await safe_send_animation(message.bot, message.chat.id, "journal", settings)
    await safe_send_sticker(message.bot, message.chat.id, "journal", settings)
    await state.set_state(JournalStates.waiting_text)
    await clean_answer(message, JOURNAL_PROMPT, main_menu(language))


@router.message(JournalStates.waiting_text, F.text)
async def journal_text(message: Message, state: FSMContext, session: AsyncSession, db_user: User, settings: Settings) -> None:
    parsed = await JournalParser(settings, message.bot).parse(message.text or "", db_user.trading_type)
    await _handle_parsed(message, state, session, db_user, settings, parsed)


@router.message(JournalStates.waiting_missing_fields, F.text)
async def journal_missing_fields(message: Message, state: FSMContext, session: AsyncSession, db_user: User, settings: Settings) -> None:
    data = await state.get_data()
    pending_text = data.get("pending_text") or ""
    merged = f"{pending_text}\nQo‘shimcha ma’lumot: {message.text or ''}"
    parsed = await JournalParser(settings, message.bot).parse(merged, db_user.trading_type)
    await _handle_parsed(message, state, session, db_user, settings, parsed)


@router.message(JournalStates.waiting_emotion, F.text)
async def journal_emotion(message: Message, state: FSMContext, session: AsyncSession, db_user: User, settings: Settings) -> None:
    data = await state.get_data()
    parsed = data.get("pending_parse") or {}
    parsed["emotion"] = _emotion_from_button(message.text or "") or "other"
    await _save_trade(message, state, session, db_user, settings, parsed)


@router.message(F.photo)
async def save_screenshot(message: Message, session: AsyncSession, db_user: User, settings: Settings) -> None:
    photo = message.photo[-1]
    latest = await JournalRepository(session).latest(db_user)
    existing = await ScreenshotRepository(session).for_trade(latest.id) if latest else []
    screenshot_type = VisionService.classify(message.caption, len(existing))
    summary = await VisionService(settings).analyze_telegram_photo(message.bot, photo.file_id, message.caption)
    await ScreenshotRepository(session).create(
        db_user,
        file_id=photo.file_id,
        file_unique_id=photo.file_unique_id,
        screenshot_type=screenshot_type,
        trade_journal_id=latest.id if latest else None,
        ai_vision_summary=summary,
    )
    await clean_answer(
        message,
        "📸 <b>Screenshot saqlandi.</b>\n\n"
        f"Turi: <b>{screenshot_type}</b>\n\n"
        f"🧠 <b>Iron AI:</b>\n{summary}",
        reply_markup=main_menu(db_user.language),
        delete_user_message=False,
    )


async def _handle_parsed(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: User,
    settings: Settings,
    parsed: dict,
) -> None:
    missing = required_missing_fields(parsed)
    if missing:
        await state.update_data(pending_parse=parsed, pending_text=parsed.get("raw_text") or message.text or "")
        await state.set_state(JournalStates.waiting_missing_fields)
        await clean_answer(
            message,
            "⚠️ Do‘stim, ma’lumot deyarli tayyor. Faqat quyidagilar yetishmayapti:\n"
            + "\n".join(f"- {item}" for item in missing)
            + "\n\nShularni yozib yuboring, keyin jurnalga saqlayman.",
            reply_markup=main_menu(db_user.language),
        )
        return
    if not parsed.get("emotion"):
        await state.update_data(pending_parse=parsed)
        await state.set_state(JournalStates.waiting_emotion)
        await clean_answer(message, "😐 Savdo paytida holatingiz qanday edi?", emotion_keyboard())
        return
    await _save_trade(message, state, session, db_user, settings, parsed)


async def _save_trade(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: User,
    settings: Settings,
    parsed: dict,
) -> None:
    trade = await JournalRepository(session).create(db_user, parsed)
    await EmotionService(session).record_trade(db_user, trade)
    await state.clear()
    if trade.net_result > 0:
        await safe_send_sticker(message.bot, message.chat.id, "profit", settings)
    elif trade.net_result < 0:
        await safe_send_sticker(message.bot, message.chat.id, "loss", settings)
    else:
        await safe_send_sticker(message.bot, message.chat.id, "success", settings)
    await clean_answer(message, _saved_message(trade), main_menu(db_user.language))


def _saved_message(trade) -> str:
    result_emoji = "✅" if trade.net_result > 0 else "❌" if trade.net_result < 0 else "➖"
    return (
        "📘 <b>Savdo jurnalingiz saqlandi</b>\n\n"
        f"📅 Sana: <b>{trade.date.isoformat()}</b>\n"
        f"💱 Instrument: <b>{trade.instrument or '-'}</b>\n"
        f"⚖️ Risk: <b>{trade.risk_percent if trade.risk_percent is not None else '-'}%</b>\n"
        f"💰 Natija: {result_emoji} <b>{signed_money(trade.net_result)}</b>\n"
        f"😐 Emotion: <b>{trade.emotion or '-'}</b>\n\n"
        "🧠 <b>Iron AI xulosasi:</b>\n"
        f"{trade.ai_summary or 'Savdo saqlandi. Keyingi safar sabab, risk va emotionni yanada aniqroq yozing.'}\n\n"
        "Bu moliyaviy maslahat emas, faqat jurnal va ta’limiy tahlil."
    )


def _emotion_from_button(text: str) -> str | None:
    lower = text.lower()
    if "tinch" in lower:
        return "calm"
    if "qo‘rq" in lower or "qorq" in lower:
        return "fear"
    if "revenge" in lower:
        return "revenge"
    if "shosh" in lower:
        return "rush"
    if "ochko" in lower:
        return "greed"
    if "oddiy" in lower:
        return "normal"
    if "boshqa" in lower:
        return "other"
    return None
