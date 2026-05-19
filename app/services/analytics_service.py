from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from typing import TYPE_CHECKING

from app.database.models import TradeJournal

if TYPE_CHECKING:
    from app.services.stats_service import JournalStats


def equity_curve(entries: list[TradeJournal]) -> list[tuple[date, float]]:
    total = 0.0
    points: list[tuple[date, float]] = []
    for entry in sorted(entries, key=lambda item: (item.date, item.id)):
        total += float(entry.net_result or 0)
        points.append((entry.date, round(total, 2)))
    return points


def instrument_pnl(entries: list[TradeJournal], limit: int = 8) -> list[tuple[str, float]]:
    grouped: dict[str, float] = defaultdict(float)
    for entry in entries:
        grouped[entry.instrument or entry.pair or entry.coin_symbol or "-"] += float(entry.net_result or 0)
    return sorted(grouped.items(), key=lambda item: item[1], reverse=True)[:limit]


def emotion_counts(entries: list[TradeJournal], limit: int = 6) -> list[tuple[str, int]]:
    counts = Counter(entry.emotion or "unknown" for entry in entries)
    return counts.most_common(limit)


def risk_buckets(entries: list[TradeJournal]) -> list[tuple[str, int]]:
    buckets = {"0-1%": 0, "1-3%": 0, "3-5%": 0, "5%+": 0, "unknown": 0}
    for entry in entries:
        risk = entry.risk_percent
        if risk is None:
            buckets["unknown"] += 1
        elif risk <= 1:
            buckets["0-1%"] += 1
        elif risk <= 3:
            buckets["1-3%"] += 1
        elif risk <= 5:
            buckets["3-5%"] += 1
        else:
            buckets["5%+"] += 1
    return [(key, value) for key, value in buckets.items() if value]


def performance_score(stats: "JournalStats") -> int:
    score = 50
    score += 20 if stats.net_pnl > 0 else -15 if stats.net_pnl < 0 else 0
    score += 10 if stats.win_rate >= 55 else -8 if stats.win_rate < 40 and stats.total_trades else 0
    score += 10 if 0 < stats.avg_risk <= 3 else -12 if stats.avg_risk > 5 else 0
    score += 5 if not stats.repeated_mistakes else -5
    return max(0, min(100, score))


def ai_action_plan(stats: "JournalStats") -> str:
    if not stats.entries:
        return (
            "Jurnal ma’lumoti hali kam. Kamida 5 ta savdo yozilgandan keyin Iron AI aniqroq xulosa beradi.\n"
            "Bugundan boshlab har bir entry sababini, risk foizini va emotionni yozing."
        )
    actions: list[str] = []
    if stats.avg_risk > 5:
        actions.append("Risk foizi yuqori. Keyingi 10 ta savdoda riskni 1-3% oralig‘ida ushlang.")
    elif stats.avg_risk == 0:
        actions.append("Risk foizi ko‘p savdolarda yozilmagan. Har bir savdodan oldin riskni jurnalga kiriting.")
    else:
        actions.append("Risk nazorati yomon emas. Shu limitni buzmaslik asosiy vazifa.")
    if stats.most_loss_emotion:
        actions.append(f"Zararli savdolarda “{stats.most_loss_emotion}” ko‘p uchragan. Shu holatda trade qilmaslik qoidasini kiriting.")
    if stats.worst_instrument:
        actions.append(f"{stats.worst_instrument} bo‘yicha riskni vaqtincha kamaytiring yoki faqat kuzatuv rejimida ishlang.")
    if stats.best_instrument:
        actions.append(f"{stats.best_instrument} bo‘yicha foyda bergan setup sabablarini alohida yozib boring.")
    actions.append("2 ta zararli savdodan keyin terminalni yopish yoki kamida 30 daqiqa tanaffus qilish qoidasini qo‘ying.")
    return "\n".join(f"{index}. {action}" for index, action in enumerate(actions[:5], 1))
