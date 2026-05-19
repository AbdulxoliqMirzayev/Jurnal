from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import DepositTransaction, TradeJournal, User, UserProfile


class DepositRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_profile(self, user: User) -> UserProfile:
        profile = await self.session.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
        if profile:
            return profile
        profile = UserProfile(user_id=user.id)
        self.session.add(profile)
        await self.session.flush()
        return profile

    async def set_initial(self, user: User, amount: float) -> UserProfile:
        profile = await self.get_profile(user)
        profile.initial_deposit = amount
        profile.deposit_current = amount
        self.session.add(DepositTransaction(user_id=user.id, amount=amount, type="initial", note="Initial deposit"))
        await self.session.flush()
        return profile

    async def add(self, user: User, amount: float, note: str | None = None) -> UserProfile:
        profile = await self.get_profile(user)
        profile.deposit_current = float(profile.deposit_current or 0) + amount
        self.session.add(DepositTransaction(user_id=user.id, amount=amount, type="add", note=note))
        await self.session.flush()
        return profile

    async def withdraw(self, user: User, amount: float, note: str | None = None) -> UserProfile:
        profile = await self.get_profile(user)
        profile.deposit_current = float(profile.deposit_current or 0) - amount
        self.session.add(DepositTransaction(user_id=user.id, amount=amount, type="withdraw", note=note))
        await self.session.flush()
        return profile

    async def set_risk(self, user: User, risk_type: str, risk_percent: float | None) -> UserProfile:
        profile = await self.get_profile(user)
        profile.risk_type = risk_type
        profile.custom_risk_percent = risk_percent
        await self.session.flush()
        return profile

    async def current_balance(self, user: User) -> float:
        profile = await self.get_profile(user)
        pnl = await self.session.scalar(select(func.sum(TradeJournal.net_result)).where(TradeJournal.user_id == user.id))
        return float(profile.deposit_current or 0) + float(pnl or 0)
