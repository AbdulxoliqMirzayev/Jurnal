from __future__ import annotations

from typing import Any

from aiogram import Bot

from app.config import Settings
from app.services.ai_service import IronAIService


class JournalParser:
    def __init__(self, settings: Settings, bot: Bot | None = None) -> None:
        self.ai = IronAIService(settings, bot)

    async def parse(self, text: str, trading_type: str | None = None) -> dict[str, Any]:
        return await self.ai.extract_journal(text, trading_type)


def required_missing_fields(data: dict[str, Any]) -> list[str]:
    missing = list(data.get("missing_fields") or [])
    labels = {
        "instrument": "Qaysi para/coin",
        "risk_percent": "Risk foizi",
        "result_type": "Natija profitmi yoki zararmi",
    }
    ordered = [labels[field] for field in ("risk_percent", "result_type", "instrument") if field in missing]
    return ordered or missing
