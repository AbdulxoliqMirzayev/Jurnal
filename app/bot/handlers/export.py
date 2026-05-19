from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, FSInputFile, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.main_menu import EXPORT_BUTTONS
from app.bot.keyboards.inline_keyboards import export_keyboard, period_keyboard
from app.bot.keyboards.reply_keyboards import main_menu
from app.database.models import User, UserProfile
from app.services.ai_service import IronAIService
from app.services.analytics_service import ai_action_plan
from app.services.export_service import ExportService
from app.services.stats_service import StatsService
from app.utils.dates import parse_period_days
from app.utils.stickers import safe_send_sticker
from app.config import Settings
from app.utils.menu_lifecycle import clean_answer, clean_callback_answer, clean_callback_document
from app.utils.message_manager import delete_tracked_messages, track_message

router = Router(name="export")


@router.message(F.text.in_(EXPORT_BUTTONS))
async def export_section(message: Message, settings: Settings) -> None:
    await safe_send_sticker(message.bot, message.chat.id, "export", settings)
    await clean_answer(message, "📄 <b>Export</b>\n\nQaysi formatda hisobot tayyorlaymiz?", export_keyboard())


@router.callback_query(F.data.startswith("export_type:"))
async def export_type(callback: CallbackQuery) -> None:
    export_kind = callback.data.split(":", 1)[1]
    await clean_callback_answer(callback, "Davrni tanlang:", period_keyboard(f"export:{export_kind}"))


@router.callback_query(F.data.startswith("export:"))
async def export_period(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    _, export_kind, period = callback.data.split(":", 2)
    labels = {"week": "1 hafta", "month": "1 oy", "3m": "3 oy", "6m": "6 oy", "all": "Barcha vaqt"}
    days = parse_period_days(period)
    stats = await StatsService(session).calculate(db_user, days, labels.get(period, period))
    profile = await session.scalar(select(UserProfile).where(UserProfile.user_id == db_user.id))
    service = ExportService(session)
    await delete_tracked_messages(callback.message.bot, callback.message.chat.id)
    try:
        await callback.message.delete()
    except Exception:
        pass
    progress = await callback.message.answer("⏳ Hisobot tayyorlanyapti, do‘stim...")
    await track_message(callback.message.chat.id, progress.message_id)
    await callback.answer()
    ai_notes = await _export_ai_notes(settings, callback.message.bot, stats)
    if export_kind == "pdf":
        path = await service.pdf(db_user, stats, profile, period, ai_notes)
    else:
        path = await service.excel(db_user, stats, profile, period, ai_notes)
    await clean_callback_document(
        callback,
        FSInputFile(path),
        caption="✅ Hisobot tayyor.\n\nBu moliyaviy maslahat emas, faqat jurnal tahlili.",
        reply_markup=main_menu(db_user.language),
        answer=False,
    )


async def _export_ai_notes(settings: Settings, bot, stats) -> str:
    context = (
        f"Period={stats.period_label}; total_trades={stats.total_trades}; win_rate={stats.win_rate}%; "
        f"net_pnl={stats.net_pnl:+.2f}; avg_risk={stats.avg_risk}%; "
        f"best={stats.best_instrument or '-'}; worst={stats.worst_instrument or '-'}; "
        f"emotion={stats.most_loss_emotion or '-'}; mistakes={', '.join(stats.repeated_mistakes) or '-'}"
    )
    prompt = (
        "PDF/Excel trading journal report uchun qisqa professional AI action plan yoz. "
        "Uzbek tilida bo‘lsin. Buy/sell signal berma. 4 ta aniq punkt: sabab, xato, yechim, keyingi hafta qoidasi."
    )
    try:
        text = await IronAIService(settings, bot).reply(prompt, "uz", context)
        return text[:1800] if text else ai_action_plan(stats)
    except Exception:
        return ai_action_plan(stats)
