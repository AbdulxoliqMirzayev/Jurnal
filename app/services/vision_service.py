from __future__ import annotations

import base64
from io import BytesIO

from aiogram import Bot
from openai import AsyncOpenAI

from app.config import Settings
from app.services.admin_alert_service import notify_admins, openai_alert_text, openai_problem_key


class VisionService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    async def analyze_telegram_photo(self, bot: Bot, file_id: str, caption: str | None = None) -> str:
        if not self.client or not self.settings.openai_vision_active:
            return self._fallback(caption)
        try:
            file = await bot.get_file(file_id)
            buffer = BytesIO()
            await bot.download_file(file.file_path, buffer)
            encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
            prompt = (
                "Screenshot asosida taxminiy trading chart tahlili qil. "
                "Aniq buy/sell signal berma. Quyidagilarni qisqa yoz: trend direction, support/resistance, "
                "possible entry zone, possible exit zone, liquidity zone, order block/FVG taxmini, risk-reward taxmini, "
                "entry mantiqiy yoki shoshilinch ko‘rinadimi, screenshot_summary. "
                "Har doim 'Screenshot asosida taxminiy tahlil' deb boshlagin."
            )
            for model in self.settings.openai_model_candidates(self.settings.resolved_openai_vision_model):
                try:
                    response = await self.client.responses.create(
                        model=model,
                        input=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "input_text", "text": prompt},
                                    {"type": "input_image", "image_url": f"data:image/jpeg;base64,{encoded}"},
                                ],
                            }
                        ],
                        max_output_tokens=900,
                    )
                    text = (response.output_text or "").strip()
                    if text:
                        return text
                except Exception as exc:
                    key = openai_problem_key(exc)
                    if key:
                        await notify_admins(bot, self.settings, key, openai_alert_text(key.replace("openai_", ""), model))
                    continue
        except Exception:
            return self._fallback(caption)
        return self._fallback(caption)

    @staticmethod
    def classify(caption: str | None, existing_count: int = 0) -> str:
        lower = (caption or "").lower()
        if any(word in lower for word in ("before", "oldin", "entrydan oldin", "kirishdan oldin")):
            return "before_trade"
        if any(word in lower for word in ("after", "keyin", "chiqishdan keyin", "yopilgandan keyin")):
            return "after_trade"
        if existing_count == 0:
            return "before_trade"
        if existing_count == 1:
            return "after_trade"
        return "extra_chart"

    @staticmethod
    def _fallback(caption: str | None = None) -> str:
        note = f"\nCaption: {caption}" if caption else ""
        return (
            "Screenshot asosida taxminiy tahlil.\n"
            "Trend, support/resistance va risk-rewardni aniq baholash uchun Vision API sozlang. "
            "Hozir file_id saqlandi va jurnal bilan bog‘landi."
            f"{note}"
        )
