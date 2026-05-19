from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from app.config import Settings
from app.utils.constants import ANIMATIONS, STICKERS

logger = logging.getLogger(__name__)


async def send_optional_sticker(bot: Bot, chat_id: int, sticker_env_key: str, settings: Settings | None = None) -> None:
    if settings and not settings.enable_stickers:
        return
    file_id = _get_setting(settings, STICKERS.get(sticker_env_key.lower(), sticker_env_key))
    if not file_id:
        return
    try:
        await bot.send_sticker(chat_id, file_id)
    except TelegramAPIError as exc:
        logger.warning("Failed to send sticker %s: %s", sticker_env_key, exc)
    except Exception as exc:
        logger.exception("Unexpected sticker error %s: %s", sticker_env_key, exc)


async def send_optional_animation(bot: Bot, chat_id: int, animation_env_key: str, settings: Settings | None = None) -> None:
    if settings and not settings.enable_animations:
        return
    file_id = _get_setting(settings, ANIMATIONS.get(animation_env_key.lower(), animation_env_key))
    if not file_id:
        return
    try:
        await bot.send_animation(chat_id, file_id)
    except TelegramAPIError as exc:
        logger.warning("Failed to send animation %s: %s", animation_env_key, exc)
    except Exception as exc:
        logger.exception("Unexpected animation error %s: %s", animation_env_key, exc)


def _get_setting(settings: Settings | None, env_key: str) -> str:
    if not settings:
        return ""
    attr = _normalize_key(env_key).lower()
    return str(getattr(settings, attr, "") or "").strip()


def _normalize_key(key: str) -> str:
    symbolic = {
        "start": "START_STICKER_ID",
        "welcome": "WELCOME_STICKER_ID",
        "journal": "JOURNAL_STICKER_ID",
        "success": "SUCCESS_STICKER_ID",
        "warning": "WARNING_STICKER_ID",
        "profit": "PROFIT_STICKER_ID",
        "loss": "LOSS_STICKER_ID",
        "risk": "RISK_STICKER_ID",
        "stats": "STATS_STICKER_ID",
        "export": "EXPORT_STICKER_ID",
        "reminder": "REMINDER_STICKER_ID",
        "emotion": "EMOTION_STICKER_ID",
        "admin": "ADMIN_STICKER_ID",
        "deposit": "DEPOSIT_STICKER_ID",
        "news": "NEWS_STICKER_ID",
        "chart": "CHART_STICKER_ID",
        "welcome_animation": "WELCOME_ANIMATION_ID",
        "writing_animation": "WRITING_ANIMATION_ID",
    }
    return STICKERS.get(key.lower()) or ANIMATIONS.get(key.lower()) or symbolic.get(key.lower(), key)


async def safe_send_sticker(bot: Bot, chat_id: int, sticker_key: str, settings: Settings | None = None) -> None:
    await send_optional_sticker(bot, chat_id, sticker_key, settings)


async def safe_send_animation(bot: Bot, chat_id: int, animation_key: str, settings: Settings | None = None) -> None:
    await send_optional_animation(bot, chat_id, animation_key, settings)
