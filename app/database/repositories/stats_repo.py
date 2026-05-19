from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ExportHistory, Reminder, TradeJournal, TradeScreenshot, User


class StatsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def admin_summary(self) -> dict[str, int | str | None]:
        now = datetime.now().astimezone()
        total_users = await self.session.scalar(select(func.count(User.id)))
        forex_users = await self.session.scalar(select(func.count(User.id)).where(User.trading_type == "forex"))
        crypto_users = await self.session.scalar(select(func.count(User.id)).where(User.trading_type == "crypto"))
        total_journals = await self.session.scalar(select(func.count(TradeJournal.id)))
        total_screenshots = await self.session.scalar(select(func.count(TradeScreenshot.id)))
        reminders_enabled = await self.session.scalar(select(func.count(Reminder.id)).where(Reminder.enabled.is_(True)))
        total_exports = await self.session.scalar(select(func.count(ExportHistory.id)))
        active_today = await self.session.scalar(
            select(func.count(User.id)).where(User.last_active_at >= now - timedelta(days=1))
        )
        active_week = await self.session.scalar(
            select(func.count(User.id)).where(User.last_active_at >= now - timedelta(days=7))
        )
        language_rows = await self.session.execute(select(User.language, func.count(User.id)).group_by(User.language))
        language_counts = {row[0]: row[1] for row in language_rows}
        most_used_language = max(language_counts, key=language_counts.get) if language_counts else None
        return {
            "total_users": int(total_users or 0),
            "active_today": int(active_today or 0),
            "active_week": int(active_week or 0),
            "forex_users": int(forex_users or 0),
            "crypto_users": int(crypto_users or 0),
            "total_journals": int(total_journals or 0),
            "total_screenshots": int(total_screenshots or 0),
            "reminders_enabled": int(reminders_enabled or 0),
            "most_used_language": most_used_language,
            "total_exports": int(total_exports or 0),
        }
