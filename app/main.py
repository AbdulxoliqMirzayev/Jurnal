from __future__ import annotations

import asyncio
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.bot.handlers import admin, ai_chat, export, feedback, journal, main_menu, reminders, risk, settings as settings_handler, start, stats, strategy
from app.bot.middlewares.auth import AuthMiddleware
from app.bot.middlewares.i18n import I18nMiddleware
from app.bot.middlewares.rate_limit import RateLimitMiddleware
from app.config import get_settings
from app.database.session import create_schema, make_engine
from app.logging_config import setup_logging
from app.services.admin_alert_service import notify_admins
from app.services.reminder_service import setup_reminder_scheduler


async def run_bot() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    if not settings.resolved_telegram_bot_token:
        raise RuntimeError("BOT_TOKEN .env ichida ko‘rsatilmagan.")
    if settings.resolved_database_url.startswith("sqlite"):
        Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(parents=True, exist_ok=True)
    Path("exports").mkdir(parents=True, exist_ok=True)

    engine = make_engine(settings)
    await create_schema(engine)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    bot = Bot(
        settings.resolved_telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(settings=settings)
    dp.update.middleware(RateLimitMiddleware())
    dp.update.middleware(AuthMiddleware(session_factory, settings))
    dp.update.middleware(I18nMiddleware())

    dp.include_router(start.router)
    dp.include_router(main_menu.router)
    dp.include_router(journal.router)
    dp.include_router(strategy.router)
    dp.include_router(risk.router)
    dp.include_router(stats.router)
    dp.include_router(export.router)
    dp.include_router(reminders.router)
    dp.include_router(settings_handler.router)
    dp.include_router(feedback.router)
    dp.include_router(admin.router)
    dp.include_router(ai_chat.router)

    scheduler = setup_reminder_scheduler(bot, session_factory, settings)
    scheduler.start()
    if not settings.openai_api_key:
        await notify_admins(
            bot,
            settings,
            "openai_missing_key",
            "🚨 <b>Iron Trade OpenAI ogohlantirish</b>\n\nOPENAI_API_KEY .env ichida kiritilmagan. Iron AI fallback rejimda ishlaydi.",
            throttle_minutes=720,
        )
    try:
        if settings.webhook_url:
            await _run_webhook(bot, dp, settings)
        else:
            await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()
        await engine.dispose()


async def _run_webhook(bot: Bot, dp: Dispatcher, settings) -> None:
    webhook_url = settings.webhook_url.rstrip("/") + settings.webhook_path
    await bot.set_webhook(webhook_url, secret_token=settings.webhook_secret or None)
    app = web.Application()

    async def health(_request):
        return web.json_response({"status": "ok", "bot": "iron_trade"})

    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.webhook_secret or None,
        handle_in_background=True,
    ).register(app, path=settings.webhook_path)
    setup_application(app, dp, bot=bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=settings.web_server_host, port=settings.port)
    await site.start()
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await bot.delete_webhook(drop_pending_updates=False)
        await runner.cleanup()


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
