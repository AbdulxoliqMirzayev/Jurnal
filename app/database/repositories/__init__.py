from app.database.repositories.deposit_repo import DepositRepository
from app.database.repositories.feedback_repo import FeedbackRepository
from app.database.repositories.journal_repo import JournalRepository
from app.database.repositories.reminder_repo import ReminderRepository
from app.database.repositories.screenshot_repo import ScreenshotRepository
from app.database.repositories.stats_repo import StatsRepository
from app.database.repositories.user_repo import UserRepository

__all__ = [
    "DepositRepository",
    "FeedbackRepository",
    "JournalRepository",
    "ReminderRepository",
    "ScreenshotRepository",
    "StatsRepository",
    "UserRepository",
]
