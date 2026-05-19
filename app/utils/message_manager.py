from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)

_tracked_messages: dict[int, list[int]] = {}


async def track_message(telegram_id: int, message_id: int) -> None:
    _tracked_messages.setdefault(telegram_id, []).append(message_id)


async def delete_tracked_messages(bot: Bot, telegram_id: int) -> None:
    for message_id in _tracked_messages.pop(telegram_id, []):
        try:
            await bot.delete_message(telegram_id, message_id)
        except TelegramBadRequest:
            continue
        except Exception as exc:
            logger.debug("Tracked message delete skipped for %s/%s: %s", telegram_id, message_id, exc)


async def clear_and_track(bot: Bot, telegram_id: int, new_message_id: int) -> None:
    await delete_tracked_messages(bot, telegram_id)
    await track_message(telegram_id, new_message_id)
