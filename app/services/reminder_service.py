from __future__ import annotations

import logging
from datetime import datetime, time
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import Settings
from app.database.models import Reminder, User
from app.utils.dates import parse_hhmm

logger = logging.getLogger(__name__)


def default_reminder_time(settings: Settings) -> time:
    return parse_hhmm(settings.reminder_default_time) or time(22, 0)


async def send_due_reminders(bot: Bot, session_factory: async_sessionmaker, sent_cache: set[str]) -> None:
    async with session_factory() as session:
        rows = await session.execute(
            select(Reminder, User)
            .join(User, User.id == Reminder.user_id)
            .where(Reminder.enabled.is_(True), User.is_blocked.is_(False))
        )
        reminders = rows.all()
    for reminder, user in reminders:
        timezone = reminder.timezone or "Asia/Tashkent"
        now = datetime.now(ZoneInfo(timezone))
        if now.time().hour != reminder.reminder_time.hour or now.time().minute != reminder.reminder_time.minute:
            continue
        key = f"{user.telegram_id}:{now.date().isoformat()}:{now.hour}:{now.minute}"
        if key in sent_cache:
            continue
        try:
            await bot.send_message(
                user.telegram_id,
                "⏰ Do‘stim, bugungi trading jurnalingizni yozdingizmi?\n\n"
                "📘 Bugungi savdolaringizni yozib qo‘ying.\n"
                "Bu sizga xatolaringizni ko‘rish va intizomni kuchaytirishga yordam beradi.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="📘 Jurnal yozish", callback_data="reminder:journal")]]
                ),
            )
            sent_cache.add(key)
        except Exception as exc:
            logger.warning("Reminder failed for %s: %s", user.telegram_id, exc)


def setup_reminder_scheduler(bot: Bot, session_factory: async_sessionmaker, settings: Settings) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.default_timezone)
    sent_cache: set[str] = set()
    scheduler.add_job(
        send_due_reminders,
        trigger=IntervalTrigger(minutes=1),
        args=[bot, session_factory, sent_cache],
        id="iron_daily_reminders",
        replace_existing=True,
        name="Iron Trade daily journal reminders",
    )
    return scheduler
