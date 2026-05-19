from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.services.stats_service import StatsService, instrument_rating_message


class InstrumentRatingService:
    def __init__(self, session: AsyncSession) -> None:
        self.stats = StatsService(session)

    async def message(self, user: User, days: int | None, label: str) -> str:
        rows = await self.stats.instrument_rows(user, days)
        return instrument_rating_message(rows, label)
