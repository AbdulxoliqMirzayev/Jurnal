from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import TradeJournal, User


class JournalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user: User, data: dict[str, Any]) -> TradeJournal:
        trade_date = data.get("date")
        if isinstance(trade_date, str):
            try:
                trade_date = date.fromisoformat(trade_date)
            except ValueError:
                trade_date = date.today()
        if not isinstance(trade_date, date):
            trade_date = date.today()
        instrument = data.get("instrument") or data.get("pair") or data.get("coin_symbol")
        net_result = float(data.get("net_result") or 0)
        profit = float(data.get("profit_amount") or (net_result if net_result > 0 else 0) or 0)
        loss = float(data.get("loss_amount") or (abs(net_result) if net_result < 0 else 0) or 0)
        result_type = data.get("result_type") or ("profit" if net_result > 0 else "loss" if net_result < 0 else "breakeven")
        entry = TradeJournal(
            user_id=user.id,
            trading_type=data.get("trading_type") or user.trading_type,
            date=trade_date,
            weekday=trade_date.strftime("%A").lower(),
            instrument=instrument,
            pair=data.get("pair"),
            coin_symbol=data.get("coin_symbol"),
            market_type=data.get("market_type"),
            session=data.get("session"),
            timeframe=data.get("timeframe"),
            trade_count=int(data.get("trade_count") or 1),
            entry_reason=data.get("entry_reason") or data.get("reason"),
            strategy_used=data.get("strategy_used"),
            risk_percent=data.get("risk_percent"),
            profit_amount=profit,
            loss_amount=loss,
            net_result=net_result,
            result_type=result_type,
            emotion=data.get("emotion"),
            emotional_note=data.get("emotional_note"),
            mistakes=data.get("mistakes") or [],
            good_decisions=data.get("good_decisions") or [],
            ai_summary=data.get("summary") or data.get("ai_summary"),
            ai_score=data.get("ai_score"),
            discipline_score=data.get("discipline_score"),
            risk_score=data.get("risk_score"),
            execution_score=data.get("execution_score"),
            raw_user_text=data.get("raw_text") or data.get("raw_user_text"),
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def latest(self, user: User) -> TradeJournal | None:
        return await self.session.scalar(
            select(TradeJournal)
            .where(TradeJournal.user_id == user.id)
            .order_by(TradeJournal.created_at.desc(), TradeJournal.id.desc())
        )

    async def list(self, user: User, days: int | None = None) -> list[TradeJournal]:
        query = select(TradeJournal).where(TradeJournal.user_id == user.id)
        if days is not None:
            start = datetime.now().astimezone().date() - timedelta(days=days - 1)
            query = query.where(TradeJournal.date >= start)
        query = query.order_by(TradeJournal.date.desc(), TradeJournal.id.desc())
        return list(await self.session.scalars(query))
