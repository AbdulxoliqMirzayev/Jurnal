from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    waiting_trading_type = State()
    waiting_strategy = State()
    waiting_deposit = State()
    waiting_custom_risk = State()


class JournalStates(StatesGroup):
    waiting_text = State()
    waiting_missing_fields = State()
    waiting_emotion = State()


class ReminderStates(StatesGroup):
    waiting_time = State()


class SettingsStates(StatesGroup):
    waiting_value = State()


class FeedbackStates(StatesGroup):
    waiting_feedback = State()


class AdminStates(StatesGroup):
    waiting_broadcast = State()
    confirm_broadcast = State()


class RiskStates(StatesGroup):
    waiting_custom_percent = State()
