from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.database.repositories.user_repo import UserRepository


class AuthMiddleware(BaseMiddleware):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession], settings: Settings) -> None:
        self.session_factory = session_factory
        self.settings = settings

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with self.session_factory() as session:
            data["session"] = session
            data["settings"] = self.settings
            telegram_user = getattr(event, "from_user", None) or data.get("event_from_user")
            if telegram_user is None and getattr(event, "message", None):
                telegram_user = getattr(event.message, "from_user", None)
            if telegram_user is None and getattr(event, "callback_query", None):
                telegram_user = getattr(event.callback_query, "from_user", None)
            if telegram_user:
                full_name = " ".join(part for part in [telegram_user.first_name, telegram_user.last_name] if part)
                repo = UserRepository(session, self.settings)
                user, _ = await repo.get_or_create(telegram_user.id, telegram_user.username, full_name or None)
                data["db_user"] = user
                data["language"] = user.language or self.settings.default_language
            else:
                data["language"] = self.settings.default_language
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
