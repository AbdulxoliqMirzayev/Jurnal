from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Bot statistikasi", callback_data="admin:stats")],
            [InlineKeyboardButton(text="🧠 OpenAI holati", callback_data="admin:openai")],
            [InlineKeyboardButton(text="📢 Reklama yuborish", callback_data="admin:broadcast")],
            [InlineKeyboardButton(text="👥 Userlar", callback_data="admin:users")],
            [InlineKeyboardButton(text="💬 Murojaatlar", callback_data="admin:feedback")],
            [InlineKeyboardButton(text="📄 Exportlar", callback_data="admin:exports")],
            [InlineKeyboardButton(text="⚙️ Admin sozlamalar", callback_data="admin:settings")],
        ]
    )


def broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yuborish", callback_data="broadcast:confirm"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="broadcast:cancel"),
            ]
        ]
    )
