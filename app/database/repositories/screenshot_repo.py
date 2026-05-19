from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import TradeScreenshot, User


class ScreenshotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user: User,
        file_id: str,
        file_unique_id: str | None,
        screenshot_type: str,
        trade_journal_id: int | None = None,
        ai_vision_summary: str | None = None,
    ) -> TradeScreenshot:
        screenshot = TradeScreenshot(
            user_id=user.id,
            trade_journal_id=trade_journal_id,
            file_id=file_id,
            file_unique_id=file_unique_id,
            screenshot_type=screenshot_type,
            ai_vision_summary=ai_vision_summary,
        )
        self.session.add(screenshot)
        await self.session.flush()
        return screenshot

    async def for_trade(self, trade_journal_id: int) -> list[TradeScreenshot]:
        rows = await self.session.scalars(
            select(TradeScreenshot)
            .where(TradeScreenshot.trade_journal_id == trade_journal_id)
            .order_by(TradeScreenshot.created_at)
        )
        return list(rows)
