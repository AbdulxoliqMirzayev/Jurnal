from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Feedback, User


class FeedbackRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user: User, text: str) -> Feedback:
        feedback = Feedback(user_id=user.id, text=text)
        self.session.add(feedback)
        await self.session.flush()
        return feedback

    async def list_new(self, limit: int = 30) -> list[Feedback]:
        rows = await self.session.scalars(
            select(Feedback).order_by(Feedback.created_at.desc()).limit(limit)
        )
        return list(rows)
