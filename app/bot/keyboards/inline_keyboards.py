from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


BACK_BUTTON = InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu:main")


def _markup(rows: list[list[InlineKeyboardButton]], *, back: bool = True) -> InlineKeyboardMarkup:
    if back:
        rows.append([BACK_BUTTON])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def language_keyboard(prefix: str = "lang") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O‘zbek", callback_data=f"{prefix}:uz"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data=f"{prefix}:en"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data=f"{prefix}:ru"),
            ]
        ]
    )


def risk_type_keyboard(prefix: str = "risk_type") -> InlineKeyboardMarkup:
    return _markup(
        [
            [
                InlineKeyboardButton(text="🟢 Conservative 1%", callback_data=f"{prefix}:conservative"),
                InlineKeyboardButton(text="🟡 Normal 3%", callback_data=f"{prefix}:normal"),
            ],
            [
                InlineKeyboardButton(text="🔴 Aggressive 5%", callback_data=f"{prefix}:aggressive"),
                InlineKeyboardButton(text="⚙️ Custom %", callback_data=f"{prefix}:custom"),
            ],
        ],
        back=not prefix.startswith("onboard"),
    )


def risk_percent_keyboard(prefix: str = "risk_calc") -> InlineKeyboardMarkup:
    return _markup(
        [
            [
                InlineKeyboardButton(text="3%", callback_data=f"{prefix}:3"),
                InlineKeyboardButton(text="5%", callback_data=f"{prefix}:5"),
                InlineKeyboardButton(text="8%", callback_data=f"{prefix}:8"),
                InlineKeyboardButton(text="10%", callback_data=f"{prefix}:10"),
            ],
            [InlineKeyboardButton(text="Custom", callback_data=f"{prefix}:custom")],
        ]
    )


def period_keyboard(prefix: str) -> InlineKeyboardMarkup:
    return _markup(
        [
            [
                InlineKeyboardButton(text="1 hafta", callback_data=f"{prefix}:week"),
                InlineKeyboardButton(text="1 oy", callback_data=f"{prefix}:month"),
            ],
            [
                InlineKeyboardButton(text="3 oy", callback_data=f"{prefix}:3m"),
                InlineKeyboardButton(text="6 oy", callback_data=f"{prefix}:6m"),
            ],
            [InlineKeyboardButton(text="Barcha vaqt", callback_data=f"{prefix}:all")],
        ]
    )


def strategy_keyboard() -> InlineKeyboardMarkup:
    return _markup(
        [
            [InlineKeyboardButton(text="📅 1 haftalik tahlil", callback_data="strategy:week")],
            [InlineKeyboardButton(text="🗓 1 oylik tahlil", callback_data="strategy:month")],
            [InlineKeyboardButton(text="📆 3 oylik tahlil", callback_data="strategy:3m")],
            [InlineKeyboardButton(text="🧾 6 oylik tahlil", callback_data="strategy:6m")],
            [InlineKeyboardButton(text="🔍 Sana bo‘yicha", callback_data="strategy:custom")],
            [InlineKeyboardButton(text="💬 Savol berish", callback_data="strategy:ask")],
        ]
    )


def stats_keyboard() -> InlineKeyboardMarkup:
    return _markup(
        [
            [
                InlineKeyboardButton(text="📅 Bugungi", callback_data="stats:today"),
                InlineKeyboardButton(text="📆 Haftalik", callback_data="stats:week"),
            ],
            [
                InlineKeyboardButton(text="🗓 Oylik", callback_data="stats:month"),
                InlineKeyboardButton(text="📊 Umumiy", callback_data="stats:all"),
            ],
            [
                InlineKeyboardButton(text="💱 Instrument bo‘yicha", callback_data="stats:instrument"),
                InlineKeyboardButton(text="😐 Emotion bo‘yicha", callback_data="stats:emotion"),
            ],
            [InlineKeyboardButton(text="⏱ Session bo‘yicha", callback_data="stats:session")],
        ]
    )


def export_keyboard() -> InlineKeyboardMarkup:
    return _markup(
        [
            [
                InlineKeyboardButton(text="📄 PDF hisobot", callback_data="export_type:pdf"),
                InlineKeyboardButton(text="📊 Excel hisobot", callback_data="export_type:excel"),
            ]
        ]
    )


def reminder_keyboard() -> InlineKeyboardMarkup:
    return _markup(
        [
            [InlineKeyboardButton(text="✅ Eslatmani yoqish", callback_data="reminder:on")],
            [InlineKeyboardButton(text="❌ Eslatmani o‘chirish", callback_data="reminder:off")],
            [InlineKeyboardButton(text="🕒 Vaqtni o‘zgartirish", callback_data="reminder:time")],
        ]
    )


def settings_keyboard() -> InlineKeyboardMarkup:
    return _markup(
        [
            [InlineKeyboardButton(text="🌐 Tilni o‘zgartirish", callback_data="settings:language")],
            [InlineKeyboardButton(text="📊 Trading turini o‘zgartirish", callback_data="settings:trading_type")],
            [InlineKeyboardButton(text="💼 Depositni o‘zgartirish", callback_data="settings:deposit_set")],
            [
                InlineKeyboardButton(text="➕ Deposit qo‘shish", callback_data="settings:deposit_add"),
                InlineKeyboardButton(text="➖ Deposit yechish", callback_data="settings:deposit_withdraw"),
            ],
            [InlineKeyboardButton(text="⚖️ Riskni o‘zgartirish", callback_data="settings:risk")],
            [InlineKeyboardButton(text="🧠 Strategiyani o‘zgartirish", callback_data="settings:strategy")],
            [InlineKeyboardButton(text="⏰ Eslatma vaqti", callback_data="settings:reminder_time")],
            [InlineKeyboardButton(text="🗑 Ma’lumotlarni tozalash", callback_data="settings:clear_confirm")],
        ]
    )


def admin_contact_keyboard(username: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"👨‍💻 Admin: @{username.lstrip('@')}", url=f"https://t.me/{username.lstrip('@')}")],
            [BACK_BUTTON],
        ]
    )


def confirm_keyboard(confirm_data: str, cancel_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=confirm_data),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data=cancel_data),
            ]
        ]
    )
