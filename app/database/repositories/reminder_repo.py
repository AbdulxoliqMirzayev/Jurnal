from __future__ import annotations

from datetime import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Reminder, User


class ReminderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(self, user: User, default_time: time | None = None, timezone: str = "Asia/Tashkent") -> Reminder:
        reminder = await self.session.scalar(select(Reminder).where(Reminder.user_id == user.id))
        if reminder:
            return reminder
        reminder = Reminder(user_id=user.id, reminder_time=default_time or time(22, 0), timezone=timezone)
        self.session.add(reminder)
        await self.session.flush()
        return reminder

    async def set_enabled(self, user: User, enabled: bool, default_time: time | None = None, timezone: str = "Asia/Tashkent") -> Reminder:
        reminder = await self.get_or_create(user, default_time, timezone)
        reminder.enabled = enabled
        await self.session.flush()
        return reminder

    async def set_time(self, user: User, reminder_time: time, timezone: str = "Asia/Tashkent") -> Reminder:
        reminder = await self.get_or_create(user, reminder_time, timezone)
        reminder.reminder_time = reminder_time
        reminder.timezone = timezone
        reminder.enabled = True
        await self.session.flush()
        return reminder

    async def enabled(self) -> list[Reminder]:
        rows = await self.session.scalars(select(Reminder).where(Reminder.enabled.is_(True)))
        return list(rows)
