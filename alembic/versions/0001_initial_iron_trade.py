"""initial iron trade schema

Revision ID: 0001_initial_iron_trade
Revises:
Create Date: 2026-05-18
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_iron_trade"
down_revision = None
branch_labels = None
depends_on = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "iron_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(255)),
        sa.Column("full_name", sa.String(255)),
        sa.Column("language", sa.String(8), nullable=False),
        sa.Column("trading_type", sa.String(16)),
        sa.Column("is_blocked", sa.Boolean(), nullable=False),
        sa.Column("last_active_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_iron_users_telegram_id", "iron_users", ["telegram_id"], unique=True)

    op.create_table(
        "iron_user_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("iron_users.id"), nullable=False),
        sa.Column("deposit_current", sa.Float(), nullable=False),
        sa.Column("initial_deposit", sa.Float(), nullable=False),
        sa.Column("risk_type", sa.String(32)),
        sa.Column("custom_risk_percent", sa.Float()),
        sa.Column("strategy_text", sa.Text()),
        sa.Column("trading_style", sa.String(128)),
        sa.Column("timeframe", sa.String(128)),
        sa.Column("favorite_instruments", sa.JSON()),
        sa.Column("market_type", sa.String(64)),
        sa.Column("leverage_usage", sa.String(128)),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("notifications_enabled", sa.Boolean(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_iron_user_profiles_user_id", "iron_user_profiles", ["user_id"], unique=True)

    op.create_table(
        "iron_strategy_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("iron_users.id"), nullable=False),
        sa.Column("trading_type", sa.String(16)),
        sa.Column("strategy_text", sa.Text()),
        sa.Column("trading_style", sa.String(128)),
        sa.Column("timeframe", sa.String(128)),
        sa.Column("instruments", sa.JSON()),
        sa.Column("risk_preference", sa.String(128)),
        sa.Column("market_type", sa.String(64)),
        sa.Column("leverage_usage", sa.String(128)),
        *timestamps(),
    )
    op.create_index("ix_iron_strategy_profiles_user_id", "iron_strategy_profiles", ["user_id"])

    op.create_table(
        "iron_deposit_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("iron_users.id"), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("type", sa.String(16), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_iron_deposit_transactions_user_id", "iron_deposit_transactions", ["user_id"])

    op.create_table(
        "iron_trade_journals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("iron_users.id"), nullable=False),
        sa.Column("trading_type", sa.String(16)),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("weekday", sa.String(16)),
        sa.Column("instrument", sa.String(64)),
        sa.Column("pair", sa.String(32)),
        sa.Column("coin_symbol", sa.String(32)),
        sa.Column("market_type", sa.String(64)),
        sa.Column("session", sa.String(32)),
        sa.Column("timeframe", sa.String(64)),
        sa.Column("trade_count", sa.Integer(), nullable=False),
        sa.Column("entry_reason", sa.Text()),
        sa.Column("strategy_used", sa.Text()),
        sa.Column("risk_percent", sa.Float()),
        sa.Column("profit_amount", sa.Float(), nullable=False),
        sa.Column("loss_amount", sa.Float(), nullable=False),
        sa.Column("net_result", sa.Float(), nullable=False),
        sa.Column("result_type", sa.String(24)),
        sa.Column("emotion", sa.String(64)),
        sa.Column("emotional_note", sa.Text()),
        sa.Column("mistakes", sa.JSON()),
        sa.Column("good_decisions", sa.JSON()),
        sa.Column("ai_summary", sa.Text()),
        sa.Column("ai_score", sa.Float()),
        sa.Column("discipline_score", sa.Float()),
        sa.Column("risk_score", sa.Float()),
        sa.Column("execution_score", sa.Float()),
        sa.Column("raw_user_text", sa.Text()),
        *timestamps(),
    )
    for column in ("user_id", "date", "instrument", "pair", "coin_symbol", "session", "emotion"):
        op.create_index(f"ix_iron_trade_journals_{column}", "iron_trade_journals", [column])

    op.create_table(
        "iron_trade_screenshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trade_journal_id", sa.Integer(), sa.ForeignKey("iron_trade_journals.id")),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("iron_users.id"), nullable=False),
        sa.Column("file_id", sa.Text(), nullable=False),
        sa.Column("file_unique_id", sa.Text()),
        sa.Column("screenshot_type", sa.String(32), nullable=False),
        sa.Column("ai_vision_summary", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_iron_trade_screenshots_trade_journal_id", "iron_trade_screenshots", ["trade_journal_id"])
    op.create_index("ix_iron_trade_screenshots_user_id", "iron_trade_screenshots", ["user_id"])

    op.create_table(
        "iron_reminders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("iron_users.id"), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("reminder_time", sa.Time(), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_iron_reminders_user_id", "iron_reminders", ["user_id"], unique=True)

    op.create_table(
        "iron_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("iron_users.id"), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_iron_feedback_user_id", "iron_feedback", ["user_id"])

    op.create_table(
        "iron_export_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("iron_users.id"), nullable=False),
        sa.Column("export_type", sa.String(16), nullable=False),
        sa.Column("period", sa.String(64), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_iron_export_history_user_id", "iron_export_history", ["user_id"])

    op.create_table(
        "iron_admin_broadcasts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("admin_id", sa.BigInteger(), nullable=False),
        sa.Column("content_type", sa.String(32), nullable=False),
        sa.Column("text", sa.Text()),
        sa.Column("file_id", sa.Text()),
        sa.Column("sent_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_table(
        "iron_emotion_stats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("iron_users.id"), nullable=False),
        sa.Column("emotion", sa.String(64), nullable=False),
        sa.Column("total_trades", sa.Integer(), nullable=False),
        sa.Column("win_count", sa.Integer(), nullable=False),
        sa.Column("loss_count", sa.Integer(), nullable=False),
        sa.Column("net_result", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_iron_emotion_stats_user_id", "iron_emotion_stats", ["user_id"])
    op.create_index("ix_iron_emotion_stats_emotion", "iron_emotion_stats", ["emotion"])


def downgrade() -> None:
    for table in [
        "iron_emotion_stats",
        "iron_admin_broadcasts",
        "iron_export_history",
        "iron_feedback",
        "iron_reminders",
        "iron_trade_screenshots",
        "iron_trade_journals",
        "iron_deposit_transactions",
        "iron_strategy_profiles",
        "iron_user_profiles",
        "iron_users",
    ]:
        op.drop_table(table)
