from __future__ import annotations

import asyncio

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.admin_keyboards import admin_keyboard, broadcast_confirm_keyboard
from app.bot.states.iron_states import AdminStates
from app.config import Settings
from app.database.models import AdminBroadcast, ExportHistory, Feedback, User
from app.database.repositories.feedback_repo import FeedbackRepository
from app.database.repositories.stats_repo import StatsRepository
from app.database.repositories.user_repo import UserRepository
from app.utils.stickers import safe_send_sticker
from app.utils.menu_lifecycle import clean_answer, clean_callback_answer

router = Router(name="admin")


@router.message(Command("admin"))
async def admin_panel(message: Message, settings: Settings) -> None:
    if not settings.is_admin_user(message.from_user.id, message.from_user.username):
        await message.answer("⛔ Admin panel faqat adminlar uchun.")
        return
    await safe_send_sticker(message.bot, message.chat.id, "admin", settings)
    await clean_answer(message, _admin_home(settings), admin_keyboard())


@router.callback_query(F.data.startswith("admin:"))
async def admin_action(callback: CallbackQuery, state: FSMContext, session: AsyncSession, settings: Settings) -> None:
    if not settings.is_admin_user(callback.from_user.id, callback.from_user.username):
        await callback.answer("Ruxsat yo‘q", show_alert=True)
        return
    action = callback.data.split(":", 1)[1]
    if action == "stats":
        stats = await StatsRepository(session).admin_summary()
        await clean_callback_answer(callback, _admin_stats(stats), admin_keyboard())
    elif action == "broadcast":
        await state.set_state(AdminStates.waiting_broadcast)
        await clean_callback_answer(
            callback,
            "📢 <b>Broadcast tayyorlash</b>\n\n"
            "Text, photo, video yoki document yuboring.\n"
            "Men avval preview ko‘rsataman, keyin tasdiqlasangiz hamma aktiv userlarga yuboraman.",
        )
    elif action == "users":
        users = await UserRepository(session, settings).active_users()
        preview = "\n".join(
            f"• {user.full_name or '-'} | @{user.username or '-'} | {user.telegram_id} | {user.trading_type or '-'}"
            for user in users[:20]
        )
        await clean_callback_answer(
            callback,
            f"👥 <b>Userlar</b>\n\nJami: <b>{len(users)}</b>\n\n{preview or 'User yo‘q.'}",
            admin_keyboard(),
        )
    elif action == "feedback":
        rows = await FeedbackRepository(session).list_new()
        await clean_callback_answer(callback, _feedback_list(rows), admin_keyboard())
    elif action == "exports":
        count = await session.scalar(select(func.count(ExportHistory.id)))
        rows = list(await session.scalars(select(ExportHistory).order_by(ExportHistory.created_at.desc()).limit(10)))
        text = (
            f"📄 <b>Exportlar</b>\n\nJami: <b>{int(count or 0)}</b>\n\n"
            + "\n".join(f"• {r.export_type} / {r.period} / user {r.user_id}" for r in rows)
            if rows
            else "📄 Exportlar yo‘q."
        )
        await clean_callback_answer(callback, text, admin_keyboard())
    elif action == "openai":
        await clean_callback_answer(callback, _openai_status(settings), admin_keyboard())
    else:
        await clean_callback_answer(callback, "⚙️ Admin sozlamalar:\n\n• ADMIN_IDS\n• ADMIN_USERNAME\n• OPENAI_API_KEY\n• Broadcast delay\n\nBular .env orqali boshqariladi.", admin_keyboard())


@router.message(AdminStates.waiting_broadcast)
async def capture_broadcast(message: Message, state: FSMContext) -> None:
    content = {"content_type": "text", "text": message.text, "file_id": None, "caption": message.caption}
    if message.photo:
        content = {"content_type": "photo", "text": message.caption, "file_id": message.photo[-1].file_id}
    elif message.video:
        content = {"content_type": "video", "text": message.caption, "file_id": message.video.file_id}
    elif message.document:
        content = {"content_type": "document", "text": message.caption, "file_id": message.document.file_id}
    await state.update_data(broadcast=content)
    await state.set_state(AdminStates.confirm_broadcast)
    await clean_answer(
        message,
        _broadcast_preview(content),
        broadcast_confirm_keyboard(),
        delete_user_message=False,
    )


@router.callback_query(F.data == "broadcast:cancel")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await clean_callback_answer(callback, "❌ Broadcast bekor qilindi.", admin_keyboard())


@router.callback_query(F.data == "broadcast:confirm")
async def broadcast_confirm(callback: CallbackQuery, state: FSMContext, session: AsyncSession, settings: Settings) -> None:
    if not settings.is_admin_user(callback.from_user.id, callback.from_user.username):
        await callback.answer("Ruxsat yo‘q", show_alert=True)
        return
    data = await state.get_data()
    content = data.get("broadcast") or {}
    users = await UserRepository(session, settings).active_users()
    sent = 0
    failed = 0
    for user in users:
        try:
            await _send_broadcast(callback.message.bot, user.telegram_id, content)
            sent += 1
            await asyncio.sleep(settings.broadcast_delay_seconds)
        except Exception:
            failed += 1
    session.add(
        AdminBroadcast(
            admin_id=callback.from_user.id,
            content_type=content.get("content_type") or "text",
            text=content.get("text"),
            file_id=content.get("file_id"),
            sent_count=sent,
            failed_count=failed,
        )
    )
    await state.clear()
    await clean_callback_answer(callback, f"✅ Broadcast yakunlandi.\nSent: <b>{sent}</b>\nFailed: <b>{failed}</b>", admin_keyboard())


async def _send_broadcast(bot, telegram_id: int, content: dict) -> None:
    content_type = content.get("content_type")
    text = content.get("text")
    file_id = content.get("file_id")
    if content_type == "photo":
        await bot.send_photo(telegram_id, file_id, caption=text)
    elif content_type == "video":
        await bot.send_video(telegram_id, file_id, caption=text)
    elif content_type == "document":
        await bot.send_document(telegram_id, file_id, caption=text)
    else:
        await bot.send_message(telegram_id, text or "")


def _admin_stats(stats: dict) -> str:
    return (
        "📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Total users: <b>{stats['total_users']}</b>\n"
        f"🟢 Active today: <b>{stats['active_today']}</b>\n"
        f"📅 Active week: <b>{stats['active_week']}</b>\n"
        f"💱 Forex users: <b>{stats['forex_users']}</b>\n"
        f"🪙 Crypto users: <b>{stats['crypto_users']}</b>\n"
        f"📘 Total journals: <b>{stats['total_journals']}</b>\n"
        f"📸 Total screenshots: <b>{stats['total_screenshots']}</b>\n"
        f"⏰ Reminders enabled: <b>{stats['reminders_enabled']}</b>\n"
        f"🌐 Most used language: <b>{stats['most_used_language'] or '-'}</b>\n"
        f"📄 Total exports: <b>{stats['total_exports']}</b>"
    )


def _admin_home(settings: Settings) -> str:
    ids = ", ".join(str(item) for item in sorted(settings.admin_id_set)) or "ID yo‘q"
    return (
        "🛡 <b>Iron Trade admin panel</b>\n\n"
        f"Admin: <b>@{settings.resolved_admin_username}</b>\n"
        f"Admin IDs: <b>{ids}</b>\n\n"
        "Bu panel faqat adminlar uchun. Oddiy userlarga user menyu chiqadi."
    )


def _openai_status(settings: Settings) -> str:
    api_key = "✅ bor" if settings.openai_api_key else "❌ yo‘q"
    text_model = settings.resolved_openai_text_model or "-"
    vision_model = settings.resolved_openai_vision_model or "-"
    return (
        "🧠 <b>OpenAI holati</b>\n\n"
        f"API key: <b>{api_key}</b>\n"
        f"Text model: <b>{text_model}</b>\n"
        f"Vision model: <b>{vision_model}</b>\n"
        f"Text active: <b>{'✅' if settings.openai_text_active else '❌'}</b>\n"
        f"Vision active: <b>{'✅' if settings.openai_vision_active else '❌'}</b>\n\n"
        "Token/quota tugasa Iron AI avtomatik adminlarga xabar yuboradi."
    )


def _broadcast_preview(content: dict) -> str:
    content_type = content.get("content_type") or "text"
    text = content.get("text") or ""
    if text and len(text) > 900:
        text = text[:900] + "..."
    return (
        "📢 <b>Broadcast preview</b>\n\n"
        f"Type: <b>{content_type}</b>\n"
        f"Text:\n{text or '-'}\n\n"
        "Yuborishni tasdiqlaysizmi?"
    )


def _feedback_list(rows: list[Feedback]) -> str:
    if not rows:
        return "💬 Murojaatlar yo‘q."
    parts = ["💬 <b>Oxirgi murojaatlar</b>\n"]
    for item in rows[:10]:
        parts.append(f"\n#{item.id} user {item.user_id}: {item.text[:120]}")
    return "".join(parts)
