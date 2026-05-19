from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.database.models import User, UserProfile


class UserRepository:
    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self.session = session
        self.settings = settings

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        return await self.session.scalar(select(User).where(User.telegram_id == telegram_id))

    async def get_or_create(self, telegram_id: int, username: str | None, full_name: str | None) -> tuple[User, bool]:
        user = await self.get_by_telegram_id(telegram_id)
        now = datetime.now().astimezone()
        if user:
            user.username = username
            user.full_name = full_name
            user.last_active_at = now
            await self.session.flush()
            return user, False
        user = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            language=(self.settings.default_language if self.settings else "uz"),
        )
        self.session.add(user)
        await self.session.flush()
        profile = UserProfile(
            user_id=user.id,
            timezone=(self.settings.default_timezone if self.settings else "Asia/Tashkent"),
        )
        self.session.add(profile)
        await self.session.flush()
        return user, True

    async def ensure_profile(self, user: User) -> UserProfile:
        profile = await self.session.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
        if profile:
            return profile
        profile = UserProfile(
            user_id=user.id,
            timezone=(self.settings.default_timezone if self.settings else "Asia/Tashkent"),
        )
        self.session.add(profile)
        await self.session.flush()
        return profile

    async def set_language(self, user: User, language: str) -> User:
        user.language = language
        await self.session.flush()
        return user

    async def set_trading_type(self, user: User, trading_type: str) -> User:
        user.trading_type = trading_type
        await self.session.flush()
        return user

    async def active_users(self) -> list[User]:
        rows = await self.session.scalars(select(User).where(User.is_blocked.is_(False)))
        return list(rows)

    async def count(self) -> int:
        value = await self.session.scalar(select(func.count(User.id)))
        return int(value or 0)
