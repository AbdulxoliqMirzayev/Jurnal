from __future__ import annotations

from app.services.stats_service import JournalStats, stats_advice


def test_stats_advice_flags_risk_and_overtrading():
    stats = JournalStats(
        period_label="test",
        journal_days=3,
        total_trades=9,
        total_profit=420,
        total_loss=180,
        net_result=240,
        win_days=2,
        loss_days=1,
        neutral_days=0,
        win_rate=66.7,
        most_traded_symbol="XAUUSD",
        best_symbol="XAUUSD",
        worst_symbol="BTCUSD",
        avg_daily_result=80,
        deposit_balance=240,
        risk_percent=6,
        risk_exceeded_days=1,
        best_reason="trend",
        avg_loss_day_trades=6,
        avg_win_day_trades=2,
    )
    advice = stats_advice(stats)
    assert "XAUUSD" in advice
    assert "overtrading" in advice
    assert "Risk limit" in advice
