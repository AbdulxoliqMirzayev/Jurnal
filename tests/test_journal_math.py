from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import Settings
from app.database.models import Base, TradeJournal, User
from app.database.session import make_engine
from app.services.stats_service import JournalStats, StatsService, stats_advice
from app.utils.finance_math import calculate_compound_projection
from app.utils.number_parser import parse_number


def test_number_parser_accepts_trading_inputs():
    assert parse_number("200$") == 200
    assert parse_number("1 000") == 1000
    assert parse_number("0.05 lot") == 0.05


def test_compound_projection_uses_forex_trading_days():
    result = calculate_compound_projection(200, 5)
    assert result["1_week"] == pytest.approx(200 * (1.05**5))
    assert result["3_months"] == pytest.approx(200 * (1.05**60))


def test_stats_advice_uses_profit_loss_context():
    stats = JournalStats(
        period_label="test",
        journal_days=3,
        total_trades=10,
        total_profit=420,
        total_loss=180,
        net_result=240,
        net_pnl=240,
        win_days=2,
        loss_days=1,
        neutral_days=0,
        win_rate=66.7,
        most_traded_symbol="XAUUSD",
        best_symbol="XAUUSD",
        worst_symbol="BTCUSD",
        avg_daily_result=80,
        risk_exceeded_days=1,
        best_reason="trend",
        avg_loss_day_trades=6,
        avg_win_day_trades=2,
    )
    advice = stats_advice(stats)
    assert "XAUUSD" in advice
    assert "overtrading" in advice
    assert "Risk limit" in advice
    assert "ijobiy" in advice


@pytest.mark.asyncio
async def test_stats_service_calculates_profit_loss_net_win_rate(tmp_path):
    settings = Settings(DATABASE_URL=f"sqlite+aiosqlite:///{tmp_path / 'stats.db'}")
    engine = make_engine(settings)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    today = date.today()
    async with session_factory() as session:
        user = User(telegram_id=555, username="tester", full_name="Test User", language="uz", trading_type="forex")
        session.add(user)
        await session.flush()
        entries = [
            TradeJournal(
                user_id=user.id,
                trading_type="forex",
                date=today - timedelta(days=1),
                weekday="monday",
                instrument="XAUUSD",
                pair="XAUUSD",
                session="london",
                timeframe="M15",
                trade_count=2,
                risk_percent=3,
                profit_amount=300,
                loss_amount=0,
                net_result=300,
                result_type="profit",
                emotion="calm",
                mistakes=[],
                good_decisions=["Plan"],
            ),
            TradeJournal(
                user_id=user.id,
                trading_type="forex",
                date=today - timedelta(days=2),
                weekday="tuesday",
                instrument="BTCUSD",
                pair="BTCUSD",
                session="new_york",
                timeframe="H1",
                trade_count=6,
                risk_percent=5,
                profit_amount=0,
                loss_amount=180,
                net_result=-180,
                result_type="loss",
                emotion="rush",
                mistakes=["Shoshilib entry qilish"],
                good_decisions=[],
            ),
            TradeJournal(
                user_id=user.id,
                trading_type="forex",
                date=today - timedelta(days=3),
                weekday="wednesday",
                instrument="XAUUSD",
                pair="XAUUSD",
                session="london",
                timeframe="M15",
                trade_count=1,
                risk_percent=2,
                profit_amount=120,
                loss_amount=0,
                net_result=120,
                result_type="profit",
                emotion="calm",
                mistakes=[],
                good_decisions=["Plan"],
            ),
        ]
        session.add_all(entries)
        await session.commit()

    async with session_factory() as session:
        user = await session.get(User, 1)
        stats = await StatsService(session).calculate(user, days=30, label="test")

    assert stats.total_profit == pytest.approx(420)
    assert stats.total_loss == pytest.approx(180)
    assert stats.net_result == pytest.approx(240)
    assert stats.net_pnl == pytest.approx(240)
    assert stats.win_rate == pytest.approx(66.7)
    assert stats.total_trades == 9
    assert stats.most_traded_symbol == "XAUUSD"
    assert stats.best_symbol == "XAUUSD"
    assert stats.worst_symbol == "BTCUSD"
    assert stats.best_session == "london"
    assert stats.worst_session == "new_york"
    assert stats.most_loss_emotion == "rush"
    await engine.dispose()
