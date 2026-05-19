from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import EmotionStats, TradeJournal, User


class EmotionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_trade(self, user: User, trade: TradeJournal) -> None:
        if not trade.emotion:
            return
        stat = await self.session.scalar(
            select(EmotionStats).where(EmotionStats.user_id == user.id, EmotionStats.emotion == trade.emotion)
        )
        if not stat:
            stat = EmotionStats(user_id=user.id, emotion=trade.emotion)
            self.session.add(stat)
        stat.total_trades += int(trade.trade_count or 1)
        if trade.result_type == "profit":
            stat.win_count += 1
        elif trade.result_type == "loss":
            stat.loss_count += 1
        stat.net_result += float(trade.net_result or 0)
        await self.session.flush()

    async def analysis(self, user: User) -> str:
        rows = list(await self.session.scalars(select(EmotionStats).where(EmotionStats.user_id == user.id)))
        if not rows:
            return "😐 Emotion tahlil uchun hali ma’lumot kam, do‘stim."
        worst = min(rows, key=lambda item: item.net_result)
        total_losses = sum(item.loss_count for item in rows) or 1
        share = round(worst.loss_count / total_losses * 100)
        return (
            "😐 <b>Emotion tahlil</b>\n\n"
            f"Zararli savdolaringizning taxminan <b>{share}%</b> qismi “{worst.emotion}” holati bilan bog‘liq.\n\n"
            "Xulosa:\n"
            "Asosiy muammo strategiya emas, savdoga kirishdagi psixologik holat bo‘lishi mumkin.\n\n"
            "Tavsiya:\n"
            "Entrydan oldin 3 daqiqa kutish va sababni yozish qoidasini kiriting."
        )
