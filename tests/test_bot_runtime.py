from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.bot.keyboards.inline_keyboards import language_keyboard
from app.bot.keyboards.reply_keyboards import main_menu
from app.bot.middlewares.auth import AuthMiddleware
from app.config import Settings
from app.database.models import Base
from app.database.session import make_engine
from app.services.ai_service import IronAIService


class FakeTelegramUser:
    id = 1001
    username = "tester"
    first_name = "Test"
    last_name = "User"


class FakeEvent:
    from_user = FakeTelegramUser()


class FakeUpdateEvent:
    from_user = None


@pytest.mark.asyncio
async def test_auth_middleware_injects_language_user_and_settings(tmp_path):
    settings = Settings(DATABASE_URL=f"sqlite+aiosqlite:///{tmp_path / 'bot.db'}")
    engine = make_engine(settings)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    middleware = AuthMiddleware(session_factory, settings)
    seen = {}

    async def handler(event, data):
        seen.update(data)
        return "ok"

    result = await middleware(handler, FakeEvent(), {})
    assert result == "ok"
    assert seen["language"] == "uz"
    assert seen["db_user"].telegram_id == FakeTelegramUser.id
    assert seen["settings"] is settings
    await engine.dispose()


@pytest.mark.asyncio
async def test_auth_middleware_uses_aiogram_event_from_user(tmp_path):
    settings = Settings(DATABASE_URL=f"sqlite+aiosqlite:///{tmp_path / 'bot_update.db'}")
    engine = make_engine(settings)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    middleware = AuthMiddleware(session_factory, settings)
    seen = {}

    async def handler(event, data):
        seen.update(data)
        return "ok"

    result = await middleware(handler, FakeUpdateEvent(), {"event_from_user": FakeTelegramUser()})
    assert result == "ok"
    assert seen["language"] == "uz"
    assert seen["db_user"].telegram_id == FakeTelegramUser.id
    await engine.dispose()


def test_keyboards_have_required_iron_trade_buttons():
    assert language_keyboard().inline_keyboard
    menu = main_menu("uz")
    button_texts = [button.text for row in menu.keyboard for button in row]
    assert "📘 Trading jurnal" in button_texts
    assert "🧠 Strategiya tahlili" in button_texts
    assert "🧮 Risk kalkulyator" in button_texts
    assert "📊 Statistika" in button_texts
    assert "📈 Instrument reytingi" in button_texts
    assert "📄 Export" in button_texts
    assert "⏰ Eslatmalar" in button_texts
    assert "⚙️ Sozlamalar" in button_texts
    assert "💬 Taklif va murojaat" in button_texts
    assert "🤖 Iron AI yordam" in button_texts


def test_openai_model_candidates_keep_primary_model_first():
    settings = Settings(OPENAI_TEXT_MODEL="gpt-5.5", OPENAI_FALLBACK_MODELS="gpt-5.2,gpt-5")
    assert settings.openai_model_candidates(settings.openai_text_model) == ["gpt-5.5", "gpt-5.2", "gpt-5"]


@pytest.mark.asyncio
async def test_iron_ai_answers_macro_and_redirects_off_topic():
    service = IronAIService(Settings(OPENAI_API_KEY=""))
    cpi_reply = await service.reply("CPI nima?", "uz")
    off_topic_reply = await service.reply("osh retsepti kerak", "uz")

    assert "CPI" in cpi_reply
    assert "yangiligi bo‘lsa" in cpi_reply
    assert "trading" in off_topic_reply
    assert "PDF/Excel" in off_topic_reply
