from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, Time, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


JsonType = JSON().with_variant(JSONB, "postgresql")


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class User(Base, TimestampMixin):
    __tablename__ = "iron_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(255))
    language: Mapped[str] = mapped_column(String(8), default="uz")
    trading_type: Mapped[str | None] = mapped_column(String(16))
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    last_active_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    profile: Mapped["UserProfile | None"] = relationship(back_populates="user", cascade="all, delete-orphan")
    strategy_profiles: Mapped[list["StrategyProfile"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    deposits: Mapped[list["DepositTransaction"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    journals: Mapped[list["TradeJournal"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    screenshots: Mapped[list["TradeScreenshot"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    reminder: Mapped["Reminder | None"] = relationship(back_populates="user", cascade="all, delete-orphan")
    feedbacks: Mapped[list["Feedback"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base, TimestampMixin):
    __tablename__ = "iron_user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("iron_users.id"), unique=True, index=True)
    deposit_current: Mapped[float] = mapped_column(Float, default=0.0)
    initial_deposit: Mapped[float] = mapped_column(Float, default=0.0)
    risk_type: Mapped[str | None] = mapped_column(String(32))
    custom_risk_percent: Mapped[float | None] = mapped_column(Float)
    strategy_text: Mapped[str | None] = mapped_column(Text)
    trading_style: Mapped[str | None] = mapped_column(String(128))
    timeframe: Mapped[str | None] = mapped_column(String(128))
    favorite_instruments: Mapped[list | None] = mapped_column(JsonType)
    market_type: Mapped[str | None] = mapped_column(String(64))
    leverage_usage: Mapped[str | None] = mapped_column(String(128))
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Tashkent")
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped[User] = relationship(back_populates="profile")


class StrategyProfile(Base, TimestampMixin):
    __tablename__ = "iron_strategy_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("iron_users.id"), index=True)
    trading_type: Mapped[str | None] = mapped_column(String(16))
    strategy_text: Mapped[str | None] = mapped_column(Text)
    trading_style: Mapped[str | None] = mapped_column(String(128))
    timeframe: Mapped[str | None] = mapped_column(String(128))
    instruments: Mapped[list | None] = mapped_column(JsonType)
    risk_preference: Mapped[str | None] = mapped_column(String(128))
    market_type: Mapped[str | None] = mapped_column(String(64))
    leverage_usage: Mapped[str | None] = mapped_column(String(128))

    user: Mapped[User] = relationship(back_populates="strategy_profiles")


class DepositTransaction(Base):
    __tablename__ = "iron_deposit_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("iron_users.id"), index=True)
    amount: Mapped[float] = mapped_column(Float)
    type: Mapped[str] = mapped_column(String(16))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="deposits")


class TradeJournal(Base, TimestampMixin):
    __tablename__ = "iron_trade_journals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("iron_users.id"), index=True)
    trading_type: Mapped[str | None] = mapped_column(String(16))
    date: Mapped[date] = mapped_column(Date, index=True)
    weekday: Mapped[str | None] = mapped_column(String(16))
    instrument: Mapped[str | None] = mapped_column(String(64), index=True)
    pair: Mapped[str | None] = mapped_column(String(32), index=True)
    coin_symbol: Mapped[str | None] = mapped_column(String(32), index=True)
    market_type: Mapped[str | None] = mapped_column(String(64))
    session: Mapped[str | None] = mapped_column(String(32), index=True)
    timeframe: Mapped[str | None] = mapped_column(String(64))
    trade_count: Mapped[int] = mapped_column(Integer, default=1)
    entry_reason: Mapped[str | None] = mapped_column(Text)
    strategy_used: Mapped[str | None] = mapped_column(Text)
    risk_percent: Mapped[float | None] = mapped_column(Float)
    profit_amount: Mapped[float] = mapped_column(Float, default=0.0)
    loss_amount: Mapped[float] = mapped_column(Float, default=0.0)
    net_result: Mapped[float] = mapped_column(Float, default=0.0)
    result_type: Mapped[str | None] = mapped_column(String(24))
    emotion: Mapped[str | None] = mapped_column(String(64), index=True)
    emotional_note: Mapped[str | None] = mapped_column(Text)
    mistakes: Mapped[list | None] = mapped_column(JsonType)
    good_decisions: Mapped[list | None] = mapped_column(JsonType)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    ai_score: Mapped[float | None] = mapped_column(Float)
    discipline_score: Mapped[float | None] = mapped_column(Float)
    risk_score: Mapped[float | None] = mapped_column(Float)
    execution_score: Mapped[float | None] = mapped_column(Float)
    raw_user_text: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates="journals")
    screenshots: Mapped[list["TradeScreenshot"]] = relationship(back_populates="trade_journal", cascade="all, delete-orphan")


class TradeScreenshot(Base):
    __tablename__ = "iron_trade_screenshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trade_journal_id: Mapped[int | None] = mapped_column(ForeignKey("iron_trade_journals.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("iron_users.id"), index=True)
    file_id: Mapped[str] = mapped_column(Text)
    file_unique_id: Mapped[str | None] = mapped_column(Text)
    screenshot_type: Mapped[str] = mapped_column(String(32), default="extra_chart")
    ai_vision_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    trade_journal: Mapped[TradeJournal | None] = relationship(back_populates="screenshots")
    user: Mapped[User] = relationship(back_populates="screenshots")


class Reminder(Base, TimestampMixin):
    __tablename__ = "iron_reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("iron_users.id"), unique=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    reminder_time: Mapped[time] = mapped_column(Time, default=time(22, 0))
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Tashkent")

    user: Mapped[User] = relationship(back_populates="reminder")


class Feedback(Base):
    __tablename__ = "iron_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("iron_users.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="feedbacks")


class ExportHistory(Base):
    __tablename__ = "iron_export_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("iron_users.id"), index=True)
    export_type: Mapped[str] = mapped_column(String(16))
    period: Mapped[str] = mapped_column(String(64))
    file_path: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AdminBroadcast(Base):
    __tablename__ = "iron_admin_broadcasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_id: Mapped[int] = mapped_column(BigInteger)
    content_type: Mapped[str] = mapped_column(String(32), default="text")
    text: Mapped[str | None] = mapped_column(Text)
    file_id: Mapped[str | None] = mapped_column(Text)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EmotionStats(Base):
    __tablename__ = "iron_emotion_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("iron_users.id"), index=True)
    emotion: Mapped[str] = mapped_column(String(64), index=True)
    total_trades: Mapped[int] = mapped_column(Integer, default=0)
    win_count: Mapped[int] = mapped_column(Integer, default=0)
    loss_count: Mapped[int] = mapped_column(Integer, default=0)
    net_result: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
