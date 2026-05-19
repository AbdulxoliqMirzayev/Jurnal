from __future__ import annotations

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from app.utils.message_manager import delete_tracked_messages, track_message


async def clean_answer(
    message: Message,
    text: str,
    reply_markup=None,
    *,
    delete_user_message: bool = True,
):
    await delete_tracked_messages(message.bot, message.chat.id)
    if delete_user_message:
        try:
            await message.delete()
        except TelegramBadRequest:
            pass
        except Exception:
            pass
    sent = await message.answer(text, reply_markup=reply_markup)
    await track_message(message.chat.id, sent.message_id)
    return sent


async def clean_callback_answer(callback: CallbackQuery, text: str, reply_markup=None):
    if not callback.message:
        await callback.answer()
        return None
    await delete_tracked_messages(callback.message.bot, callback.message.chat.id)
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    except Exception:
        pass
    sent = await callback.message.answer(text, reply_markup=reply_markup)
    await track_message(callback.message.chat.id, sent.message_id)
    await callback.answer()
    return sent


async def clean_callback_document(callback: CallbackQuery, document, caption: str, reply_markup=None, *, answer: bool = True):
    if not callback.message:
        if answer:
            await callback.answer()
        return None
    await delete_tracked_messages(callback.message.bot, callback.message.chat.id)
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    except Exception:
        pass
    sent = await callback.message.answer_document(document, caption=caption, reply_markup=reply_markup)
    await track_message(callback.message.chat.id, sent.message_id)
    if answer:
        await callback.answer()
    return sent
