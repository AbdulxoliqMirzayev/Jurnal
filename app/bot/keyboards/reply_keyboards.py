from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_JOURNAL = "📘 Trading jurnal"
BTN_STRATEGY = "🧠 Strategiya tahlili"
BTN_RISK = "🧮 Risk kalkulyator"
BTN_STATS = "📊 Statistika"
BTN_RATING = "📈 Instrument reytingi"
BTN_EXPORT = "📄 Export"
BTN_REMINDERS = "⏰ Eslatmalar"
BTN_SETTINGS = "⚙️ Sozlamalar"
BTN_FEEDBACK = "💬 Taklif va murojaat"
BTN_AI_HELP = "🤖 Iron AI yordam"

MAIN_MENU_BUTTONS = {
    BTN_JOURNAL,
    BTN_STRATEGY,
    BTN_RISK,
    BTN_STATS,
    BTN_RATING,
    BTN_EXPORT,
    BTN_REMINDERS,
    BTN_SETTINGS,
    BTN_FEEDBACK,
    BTN_AI_HELP,
}


def main_menu(language: str | None = "uz") -> ReplyKeyboardMarkup:
    placeholders = {
        "uz": "Savol yozing yoki bo‘lim tanlang...",
        "en": "Ask a question or choose a section...",
        "ru": "Напишите вопрос или выберите раздел...",
    }
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_JOURNAL), KeyboardButton(text=BTN_STRATEGY)],
            [KeyboardButton(text=BTN_RISK), KeyboardButton(text=BTN_STATS)],
            [KeyboardButton(text=BTN_RATING), KeyboardButton(text=BTN_EXPORT)],
            [KeyboardButton(text=BTN_REMINDERS), KeyboardButton(text=BTN_SETTINGS)],
            [KeyboardButton(text=BTN_FEEDBACK), KeyboardButton(text=BTN_AI_HELP)],
        ],
        resize_keyboard=True,
        input_field_placeholder=placeholders.get(language or "uz", placeholders["uz"]),
    )


def trading_type_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="💱 Forex"), KeyboardButton(text="🪙 Crypto")]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def emotion_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="😌 Tinch edim"), KeyboardButton(text="😰 Qo‘rqdim")],
            [KeyboardButton(text="😡 Revenge trade"), KeyboardButton(text="🤯 Shoshildim")],
            [KeyboardButton(text="🤑 Ochko‘zlik qildim"), KeyboardButton(text="😐 Oddiy holat")],
            [KeyboardButton(text="✍️ Boshqa")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
