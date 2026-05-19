from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import TradeJournal, User
from app.database.repositories.journal_repo import JournalRepository
from app.services.analytics_service import ai_action_plan, performance_score
from app.utils.formatters import signed_money


@dataclass(slots=True)
class JournalStats:
    period_label: str
    journal_days: int = 0
    total_trades: int = 0
    win_count: int = 0
    loss_count: int = 0
    breakeven_count: int = 0
    win_days: int = 0
    loss_days: int = 0
    neutral_days: int = 0
    win_rate: float = 0.0
    net_pnl: float = 0.0
    net_result: float = 0.0
    total_profit: float = 0.0
    total_loss: float = 0.0
    avg_risk: float = 0.0
    best_instrument: str | None = None
    worst_instrument: str | None = None
    most_traded_symbol: str | None = None
    best_symbol: str | None = None
    worst_symbol: str | None = None
    best_session: str | None = None
    worst_session: str | None = None
    most_loss_emotion: str | None = None
    repeated_mistakes: list[str] = field(default_factory=list)
    avg_daily_result: float = 0.0
    deposit_balance: float | None = None
    risk_percent: float | None = None
    risk_exceeded_days: int = 0
    best_reason: str | None = None
    avg_loss_day_trades: float = 0.0
    avg_win_day_trades: float = 0.0
    entries: list[TradeJournal] = field(default_factory=list)


class StatsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def entries(self, user: User, days: int | None = None) -> list[TradeJournal]:
        return await JournalRepository(self.session).list(user, days)

    async def calculate(self, user: User, profile_or_days=None, days: int | None = None, label: str = "Umumiy") -> JournalStats:
        if isinstance(days, str):
            label = days
            days = profile_or_days
        elif isinstance(profile_or_days, int) or profile_or_days is None:
            days = profile_or_days
        entries = await self.entries(user, days)
        result_count = Counter(entry.result_type for entry in entries)
        total_trade_count = sum(int(entry.trade_count or 1) for entry in entries)
        win = int(result_count.get("profit", 0))
        loss = int(result_count.get("loss", 0))
        breakeven = int(result_count.get("breakeven", 0))
        total_profit = sum(float(entry.profit_amount or 0) for entry in entries)
        total_loss = sum(float(entry.loss_amount or 0) for entry in entries)
        net = sum(float(entry.net_result or 0) for entry in entries)
        risks = [float(entry.risk_percent) for entry in entries if entry.risk_percent is not None]
        instrument_net: dict[str, float] = defaultdict(float)
        session_net: dict[str, float] = defaultdict(float)
        loss_emotions = Counter()
        mistake_counter = Counter()
        for entry in entries:
            instrument = entry.instrument or entry.pair or entry.coin_symbol or "-"
            instrument_net[instrument] += float(entry.net_result or 0)
            if entry.session:
                session_net[entry.session] += float(entry.net_result or 0)
            if entry.result_type == "loss" and entry.emotion:
                loss_emotions[entry.emotion] += 1
            for mistake in entry.mistakes or []:
                mistake_counter[str(mistake)] += 1
        total_rows = len(entries)
        return JournalStats(
            period_label=label,
            journal_days=len({entry.date.isoformat() for entry in entries}),
            total_trades=total_trade_count,
            win_count=win,
            loss_count=loss,
            breakeven_count=breakeven,
            win_days=win,
            loss_days=loss,
            neutral_days=breakeven,
            win_rate=round(win / total_rows * 100, 1) if total_rows else 0.0,
            net_pnl=net,
            net_result=net,
            total_profit=total_profit,
            total_loss=total_loss,
            avg_risk=round(sum(risks) / len(risks), 2) if risks else 0.0,
            best_instrument=max(instrument_net, key=instrument_net.get) if instrument_net else None,
            worst_instrument=min(instrument_net, key=instrument_net.get) if instrument_net else None,
            most_traded_symbol=Counter(entry.instrument or entry.pair or entry.coin_symbol or "-" for entry in entries).most_common(1)[0][0] if entries else None,
            best_symbol=max(instrument_net, key=instrument_net.get) if instrument_net else None,
            worst_symbol=min(instrument_net, key=instrument_net.get) if instrument_net else None,
            best_session=max(session_net, key=session_net.get) if session_net else None,
            worst_session=min(session_net, key=session_net.get) if session_net else None,
            most_loss_emotion=loss_emotions.most_common(1)[0][0] if loss_emotions else None,
            repeated_mistakes=[name for name, _ in mistake_counter.most_common(5)],
            entries=entries,
        )

    async def ai_context(self, user: User, days: int = 30) -> str:
        stats = await self.calculate(user, days, f"Oxirgi {days} kun")
        return (
            f"{stats.period_label}: trades={stats.total_trades}, win_rate={stats.win_rate}%, "
            f"net={stats.net_pnl:+.2f}$, best={stats.best_instrument or '-'}, "
            f"worst={stats.worst_instrument or '-'}, emotion={stats.most_loss_emotion or '-'}"
        )

    async def instrument_rows(self, user: User, days: int | None = None) -> list[dict[str, object]]:
        entries = await self.entries(user, days)
        grouped: dict[str, list[TradeJournal]] = defaultdict(list)
        for entry in entries:
            grouped[entry.instrument or entry.pair or entry.coin_symbol or "-"].append(entry)
        rows = []
        for instrument, items in grouped.items():
            wins = sum(1 for item in items if item.result_type == "profit")
            losses = sum(1 for item in items if item.result_type == "loss")
            net = sum(float(item.net_result or 0) for item in items)
            risks = [float(item.risk_percent) for item in items if item.risk_percent is not None]
            mistakes = Counter(m for item in items for m in (item.mistakes or []))
            emotions = Counter(item.emotion for item in items if item.result_type == "loss" and item.emotion)
            rows.append(
                {
                    "instrument": instrument,
                    "total": sum(int(item.trade_count or 1) for item in items),
                    "wins": wins,
                    "losses": losses,
                    "win_rate": round(wins / len(items) * 100, 1) if items else 0.0,
                    "net": net,
                    "avg_risk": round(sum(risks) / len(risks), 2) if risks else 0.0,
                    "best_result": max((float(item.net_result or 0) for item in items), default=0.0),
                    "worst_result": min((float(item.net_result or 0) for item in items), default=0.0),
                    "mistake": mistakes.most_common(1)[0][0] if mistakes else "-",
                    "emotion": emotions.most_common(1)[0][0] if emotions else "-",
                }
            )
        return sorted(rows, key=lambda row: float(row["net"]), reverse=True)

    async def breakdown(self, user: User, key: str, days: int | None = None) -> list[tuple[str, int, float]]:
        entries = await self.entries(user, days)
        grouped: dict[str, list[TradeJournal]] = defaultdict(list)
        for entry in entries:
            value = getattr(entry, key, None) or "-"
            grouped[str(value)].append(entry)
        rows = []
        for name, items in grouped.items():
            rows.append((name, sum(int(item.trade_count or 1) for item in items), sum(float(item.net_result or 0) for item in items)))
        return sorted(rows, key=lambda row: row[2], reverse=True)


def stats_message(stats: JournalStats) -> str:
    score = performance_score(stats)
    return (
        f"📊 <b>{stats.period_label} statistika</b>\n\n"
        f"🧭 Discipline score: <b>{score}/100</b>\n"
        f"🔢 Savdolar: <b>{stats.total_trades} ta</b>\n"
        f"✅ Foydali: <b>{stats.win_count} ta</b>\n"
        f"❌ Zararli: <b>{stats.loss_count} ta</b>\n"
        f"➖ Breakeven: <b>{stats.breakeven_count} ta</b>\n"
        f"🎯 Win rate: <b>{stats.win_rate:.1f}%</b>\n"
        f"💰 Net natija: <b>{signed_money(stats.net_pnl)}</b>\n"
        f"⚖️ O‘rtacha risk: <b>{stats.avg_risk:.1f}%</b>\n\n"
        f"🥇 Eng yaxshi instrument: <b>{stats.best_instrument or '-'}</b>\n"
        f"⚠️ Eng zaif instrument: <b>{stats.worst_instrument or '-'}</b>\n\n"
        f"😐 Eng zararli emotion: <b>{stats.most_loss_emotion or '-'}</b>\n"
        f"⏱ Eng yaxshi sessiya: <b>{stats.best_session or '-'}</b>\n"
        f"📉 Eng yomon sessiya: <b>{stats.worst_session or '-'}</b>\n\n"
        f"🧠 <b>Iron AI xulosasi:</b>\n{stats_advice(stats)}\n\n"
        f"🎯 <b>Keyingi action plan:</b>\n{ai_action_plan(stats)}"
    )


def stats_advice(stats: JournalStats) -> str:
    if not stats.entries and not stats.total_trades:
        return "Do‘stim, hali jurnal ma’lumotlari kam. 3-5 ta savdo yozsangiz, aniqroq tahlil qilaman."
    lines: list[str] = []
    best = stats.best_instrument or stats.best_symbol
    if best:
        lines.append(f"Siz {best} instrumentida yaxshiroq natija ko‘rsatgansiz.")
    if stats.avg_loss_day_trades > stats.avg_win_day_trades and stats.avg_loss_day_trades > 0:
        lines.append("Zararli kunlarda trade soni ko‘paygan. Bu overtrading belgisi bo‘lishi mumkin.")
    if stats.best_reason:
        lines.append(f"{stats.best_reason} sababli ochilgan savdolar yaxshiroq natija bergan.")
    if stats.risk_exceeded_days:
        lines.append("Risk limitdan oshgan kunlar bor. Risk managementni qat’iylashtiring.")
    net = stats.net_pnl if stats.net_pnl else stats.net_result
    if net > 0:
        lines.append("Umumiy natija ijobiy. Endi foyda bergan setup va sessiyalarni takrorlash muhim.")
    elif net < 0:
        lines.append("Natija salbiy. Avval riskni kamaytirib, entry sababini yozmasdan savdoga kirmang.")
    else:
        lines.append("Natija neytral. Jurnal davom etsa, kuchli va zaif tomonlar aniqroq ko‘rinadi.")
    if stats.most_loss_emotion:
        lines.append(f"Zararli savdolarda ko‘p uchragan emotion: {stats.most_loss_emotion}.")
    if stats.repeated_mistakes:
        lines.append(f"Takroriy xato: {stats.repeated_mistakes[0]}.")
    return "\n".join(lines) + "\n\nBu moliyaviy maslahat emas, faqat jurnal tahlili."


async def strategy_analysis_message(service: StatsService, user: User, days: int | None, label: str) -> str:
    stats = await service.calculate(user, days, label)
    return (
        "🧠 <b>Iron AI strategiya tahlili</b>\n\n"
        f"📅 Davr: <b>{label}</b>\n"
        f"🔢 Savdolar soni: <b>{stats.total_trades} ta</b>\n"
        f"✅ Foydali: <b>{stats.win_count} ta</b>\n"
        f"❌ Zararli: <b>{stats.loss_count} ta</b>\n"
        f"➖ Breakeven: <b>{stats.breakeven_count} ta</b>\n"
        f"🎯 Win rate: <b>{stats.win_rate:.1f}%</b>\n"
        f"💰 Net natija: <b>{signed_money(stats.net_pnl)}</b>\n\n"
        "<b>Kuchli tomonlar:</b>\n"
        f"✅ {stats.best_instrument or 'Aniqlash uchun jurnal ma’lumoti kerak'} instrumentida nisbatan yaxshi natija\n"
        f"✅ {stats.best_session or 'Eng yaxshi sessiya hali aniqlanmadi'} sessiyasida tartib kuchliroq\n"
        f"✅ O‘rtacha risk {stats.avg_risk:.1f}% atrofida\n\n"
        "<b>Zaif tomonlar:</b>\n"
        f"⚠️ {stats.worst_instrument or 'Zaif instrument hali aniqlanmadi'} bo‘yicha ehtiyot bo‘ling\n"
        f"⚠️ {stats.most_loss_emotion or 'Emotion'} zararli savdolarga ta’sir qilgan bo‘lishi mumkin\n"
        f"⚠️ {stats.repeated_mistakes[0] if stats.repeated_mistakes else 'Entry sababi har safar aniq yozilishi kerak'}\n\n"
        "<b>Aniq tavsiya:</b>\n"
        "1. 2 ta zararli savdodan keyin savdoni to‘xtating.\n"
        "2. Entrydan oldin sababni jurnalga yozing.\n"
        "3. Risk foizini savdodan oldin belgilang.\n"
        "4. Revenge yoki shoshilish bo‘lsa, savdo qilmang.\n\n"
        "Savolingiz bo‘lsa, do‘stim, bemalol so‘rang. Birga tahlil qilamiz."
    )


def instrument_rating_message(rows: list[dict[str, object]], label: str) -> str:
    if not rows:
        return "📈 <b>Instrument reytingi</b>\n\nHali yetarli jurnal ma’lumoti yo‘q, do‘stim."
    medals = ["🥇", "🥈", "🥉"]
    parts = [f"📈 <b>Instrument reytingi</b>\n\nDavr: <b>{label}</b>\n"]
    for index, row in enumerate(rows[:5], 1):
        medal = medals[index - 1] if index <= len(medals) else "▫️"
        parts.append(
            f"\n{medal} <b>{index}. {row['instrument']}</b>\n"
            f"✅ Win rate: <b>{row['win_rate']}%</b>\n"
            f"💰 Net natija: <b>{signed_money(float(row['net']))}</b>\n"
            f"⚖️ O‘rtacha risk: <b>{row['avg_risk']}%</b>\n"
            f"🧠 Xulosa: {'Tartibli natija ko‘ringan.' if float(row['net']) >= 0 else 'Riskni pasaytirib kuzatish kerak.'}\n"
        )
    weakest = rows[-1]
    parts.append(
        f"\n⚠️ <b>Eng zaif instrument:</b>\n{weakest['instrument']}\n"
        f"❌ Net natija: <b>{signed_money(float(weakest['net']))}</b>\n"
        f"Sabab: {weakest['mistake']}\n\n"
        "Iron AI tavsiyasi:\n"
        "Do‘stim, ijobiy statistikaga ega instrumentlarda rejangizni takrorlang, zaif instrumentlarda esa riskni kamaytiring yoki kuzatuv rejimida ishlang.\n\n"
        "Bu moliyaviy maslahat emas, faqat sizning trading jurnalingiz asosidagi tahlil."
    )
    return "".join(parts)
