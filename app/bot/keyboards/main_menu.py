from __future__ import annotations

from app.bot.keyboards.reply_keyboards import (
    BTN_AI_HELP,
    BTN_EXPORT,
    BTN_FEEDBACK,
    BTN_JOURNAL,
    BTN_RATING,
    BTN_REMINDERS,
    BTN_RISK,
    BTN_SETTINGS,
    BTN_STATS,
    BTN_STRATEGY,
    MAIN_MENU_BUTTONS,
)

JOURNAL_BUTTONS = {BTN_JOURNAL, "📘 Trading Jurnal", "📒 Trading jurnal"}
STRATEGY_BUTTONS = {BTN_STRATEGY, "🧠 Strategiya Analizi", "🧠 Strategiya analysis"}
RISK_BUTTONS = {BTN_RISK, "🔢 Kalkulator", "🧮 Kalkulator"}
STATS_BUTTONS = {BTN_STATS}
RATING_BUTTONS = {BTN_RATING}
EXPORT_BUTTONS = {BTN_EXPORT}
REMINDER_BUTTONS = {BTN_REMINDERS}
SETTINGS_BUTTONS = {BTN_SETTINGS}
FEEDBACK_BUTTONS = {BTN_FEEDBACK}
AI_HELP_BUTTONS = {BTN_AI_HELP}

ALL_MENU_BUTTONS = (
    MAIN_MENU_BUTTONS
    | JOURNAL_BUTTONS
    | STRATEGY_BUTTONS
    | RISK_BUTTONS
    | STATS_BUTTONS
    | RATING_BUTTONS
    | EXPORT_BUTTONS
    | REMINDER_BUTTONS
    | SETTINGS_BUTTONS
    | FEEDBACK_BUTTONS
    | AI_HELP_BUTTONS
)
MENU_BUTTON_MAP = {
    **{button: "journal" for button in JOURNAL_BUTTONS},
    **{button: "strategy" for button in STRATEGY_BUTTONS},
    **{button: "risk" for button in RISK_BUTTONS},
    **{button: "stats" for button in STATS_BUTTONS},
    **{button: "rating" for button in RATING_BUTTONS},
    **{button: "export" for button in EXPORT_BUTTONS},
    **{button: "reminders" for button in REMINDER_BUTTONS},
    **{button: "settings" for button in SETTINGS_BUTTONS},
    **{button: "feedback" for button in FEEDBACK_BUTTONS},
    **{button: "ai_help" for button in AI_HELP_BUTTONS},
}
