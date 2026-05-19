from __future__ import annotations

from functools import lru_cache
from typing import Iterable

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    bot_token: str = Field(default="", alias="BOT_TOKEN")

    admin_id: str = Field(default="", alias="ADMIN_ID")
    admin_ids: str = Field(default="", alias="ADMIN_IDS")
    admin_chat_id: str = Field(default="", alias="ADMIN_CHAT_ID")
    admin_username: str = Field(default="mirzayev_ai", alias="ADMIN_USERNAME")
    admin_contact_username: str = Field(default="mirzayev_ai", alias="ADMIN_CONTACT_USERNAME")

    database_url: str = Field(default="", alias="DATABASE_URL")
    db_path: str = Field(default="data/iron_trade.db", alias="DB_PATH")
    database_pool_size: int = Field(default=10, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, alias="DATABASE_MAX_OVERFLOW")
    database_pool_recycle: int = Field(default=1800, alias="DATABASE_POOL_RECYCLE")
    redis_url: str = Field(default="", alias="REDIS_URL")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="", alias="OPENAI_MODEL")
    openai_text_model: str = Field(default="gpt-5.5", alias="OPENAI_TEXT_MODEL")
    openai_vision_model: str = Field(default="gpt-5.5", alias="OPENAI_VISION_MODEL")
    openai_fallback_models: str = Field(default="gpt-5.4,gpt-5.3-codex,gpt-5.2", alias="OPENAI_FALLBACK_MODELS")
    openai_temperature: float = Field(default=0.2, alias="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(default=3500, alias="OPENAI_MAX_TOKENS")
    enable_vision_analysis: bool = Field(default=True, alias="ENABLE_VISION_ANALYSIS")

    default_language: str = Field(default="uz", alias="DEFAULT_LANGUAGE")
    default_timezone: str = Field(default="Asia/Tashkent", alias="DEFAULT_TIMEZONE")
    reminder_default_time: str = Field(default="22:00", alias="REMINDER_DEFAULT_TIME")
    app_env: str = Field(default="production", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    webhook_url: str = Field(default="", alias="WEBHOOK_URL")
    webhook_path: str = Field(default="/webhook", alias="WEBHOOK_PATH")
    webhook_secret: str = Field(default="", alias="WEBHOOK_SECRET")
    web_server_host: str = Field(default="0.0.0.0", alias="WEB_SERVER_HOST")
    port: int = Field(default=8080, alias="PORT")

    broadcast_batch_size: int = Field(default=25, alias="BROADCAST_BATCH_SIZE")
    broadcast_delay_seconds: float = Field(default=1, alias="BROADCAST_DELAY_SECONDS")

    enable_stickers: bool = Field(default=True, alias="ENABLE_STICKERS")
    enable_animations: bool = Field(default=True, alias="ENABLE_ANIMATIONS")
    welcome_sticker_id: str = Field(default="", alias="WELCOME_STICKER_ID")
    journal_sticker_id: str = Field(default="", alias="JOURNAL_STICKER_ID")
    success_sticker_id: str = Field(default="", alias="SUCCESS_STICKER_ID")
    warning_sticker_id: str = Field(default="", alias="WARNING_STICKER_ID")
    profit_sticker_id: str = Field(default="", alias="PROFIT_STICKER_ID")
    loss_sticker_id: str = Field(default="", alias="LOSS_STICKER_ID")
    risk_sticker_id: str = Field(default="", alias="RISK_STICKER_ID")
    stats_sticker_id: str = Field(default="", alias="STATS_STICKER_ID")
    export_sticker_id: str = Field(default="", alias="EXPORT_STICKER_ID")
    reminder_sticker_id: str = Field(default="", alias="REMINDER_STICKER_ID")
    emotion_sticker_id: str = Field(default="", alias="EMOTION_STICKER_ID")
    admin_sticker_id: str = Field(default="", alias="ADMIN_STICKER_ID")

    welcome_animation_id: str = Field(default="", alias="WELCOME_ANIMATION_ID")
    journal_animation_id: str = Field(default="", alias="JOURNAL_ANIMATION_ID")
    writing_animation_id: str = Field(default="", alias="WRITING_ANIMATION_ID")
    profit_animation_id: str = Field(default="", alias="PROFIT_ANIMATION_ID")
    loss_animation_id: str = Field(default="", alias="LOSS_ANIMATION_ID")
    stats_animation_id: str = Field(default="", alias="STATS_ANIMATION_ID")
    export_animation_id: str = Field(default="", alias="EXPORT_ANIMATION_ID")
    reminder_animation_id: str = Field(default="", alias="REMINDER_ANIMATION_ID")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", populate_by_name=True)

    @property
    def admin_id_set(self) -> set[int]:
        return set(_parse_ints(",".join(part for part in [self.admin_ids, self.admin_id, self.admin_chat_id] if part)))

    @property
    def resolved_admin_username(self) -> str:
        return (self.admin_username or self.admin_contact_username or "mirzayev_ai").lstrip("@")

    @property
    def resolved_telegram_bot_token(self) -> str:
        return self.telegram_bot_token or self.bot_token

    @property
    def resolved_openai_text_model(self) -> str:
        return self.openai_model or self.openai_text_model

    @property
    def resolved_openai_vision_model(self) -> str:
        return self.openai_model or self.openai_vision_model

    @property
    def openai_text_active(self) -> bool:
        return bool(self.openai_api_key and self.resolved_openai_text_model)

    @property
    def openai_vision_active(self) -> bool:
        return bool(self.openai_api_key and self.resolved_openai_vision_model and self.enable_vision_analysis)

    @property
    def redis_active(self) -> bool:
        return bool(self.redis_url)

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return f"sqlite+aiosqlite:///{self.db_path}"

    def openai_model_candidates(self, primary: str | None) -> list[str]:
        output: list[str] = []
        for model in [primary or "", *list(_parse_strings(self.openai_fallback_models))]:
            if model and model not in output:
                output.append(model)
        return output

    def is_admin(self, telegram_id: int | str) -> bool:
        try:
            return int(telegram_id) in self.admin_id_set
        except (TypeError, ValueError):
            return False

    def is_admin_user(self, telegram_id: int | str | None, username: str | None = None) -> bool:
        if telegram_id is not None and self.is_admin(telegram_id):
            return True
        clean_username = (username or "").lstrip("@").lower()
        return bool(clean_username and clean_username == self.resolved_admin_username.lower())

    def daily_limit_for(self, action: str) -> int:
        return 0


def _parse_ints(raw: str) -> Iterable[int]:
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            yield int(part)
        except ValueError:
            continue


def _parse_strings(raw: str) -> Iterable[str]:
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if part:
            yield part


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
