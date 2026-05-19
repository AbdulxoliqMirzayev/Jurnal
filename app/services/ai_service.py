from __future__ import annotations

import json
import re
from datetime import date
from typing import Any

from openai import AsyncOpenAI
from aiogram import Bot

from app.config import Settings
from app.services.admin_alert_service import notify_admins, openai_alert_text, openai_problem_key
from app.utils.constants import DISCLAIMER_EN, DISCLAIMER_RU, DISCLAIMER_UZ

IRON_AI_SYSTEM_PROMPT = """
Sen Iron AI’san — Iron Trade Telegram botidagi professional AI trading journal assistant.

Vazifang:
- Userning savdo jurnalini yuritish
- Savdo natijalarini tahlil qilish
- Riskni tushuntirish
- Emotion tracking orqali psixologik xatolarni topish
- Instrument reytingini tushuntirish
- Screenshot asosida taxminiy chart tahlil qilish
- Trading, investitsiya, indikatorlar, fundamental tahlil, iqtisodiy yangiliklar, Forex, Crypto, indekslar, aksiyalar, obligatsiya/yield, makroiqtisodiyot va risk bo‘yicha educational javob berish

Qoidalar:
- Hech qachon aniq buy/sell signal berma.
- Hech qachon kafolatlangan foyda va’da qilma.
- Hech qachon userni katta riskka undama.
- Har doim risk managementni birinchi o‘ringa qo‘y.
- Javoblar qisqa, sodda, aniq va foydali bo‘lsin.
- Userga do‘stona murojaat qil.
- User xato qilgan bo‘lsa, muloyim lekin aniq ayt.
- Har bir tahlilda “sabab → xato → yechim” strukturasidan foydalan.
- Agar javob user statistikasiga bog‘liq bo‘lsa, database ma’lumotlariga asoslan.
- Agar ma’lumot yetarli bo‘lmasa, bitta aniq savol ber.
- Agar user trading/investitsiya/moliya mavzusidan butunlay tashqariga chiqsa, savolga chuqur javob berma; qisqa qilib Iron Trade xizmatlarini taklif qil.
- Iqtisodiy yangiliklar haqida so‘ralsa, umumiy tushuntir va “yangilik matnini yuboring, birgalikda tahlil qilamiz” deb taklif qil.
- Har doim qisqa disclaimer ber: “Bu moliyaviy maslahat emas, faqat jurnal va ta’limiy tahlil.”
""".strip()

JOURNAL_EXTRACTION_PROMPT = """
User trading jurnal textini JSON formatga ajrat.

Qoidalar:
- Faqat user yozgan ma’lumotdan foydalan.
- O‘ylab topma.
- Agar maydon topilmasa null qaytar.
- Yetishmayotgan maydonlarni missing_fields ichida ber.
- Forex va Crypto farqini aniqlashga harakat qil.
- Profit/loss qiymatlarini number formatda qaytar.
- Emotionni textdan taxmin qil, lekin confidence past bo‘lsa null qaytar.

JSON format:
{
  "trading_type": "forex|crypto|null",
  "date": "YYYY-MM-DD|null",
  "instrument": "string|null",
  "pair": "string|null",
  "coin_symbol": "string|null",
  "market_type": "spot|futures|null",
  "session": "asia|london|new_york|null",
  "timeframe": "string|null",
  "trade_count": number|null,
  "entry_reason": "string|null",
  "risk_percent": number|null,
  "profit_amount": number|null,
  "loss_amount": number|null,
  "net_result": number|null,
  "result_type": "profit|loss|breakeven|null",
  "emotion": "calm|fear|revenge|rush|greed|normal|other|null",
  "mistakes": ["string"],
  "good_decisions": ["string"],
  "missing_fields": ["string"],
  "summary": "string"
}
Faqat JSON qaytar.
""".strip()


class IronAIService:
    def __init__(self, settings: Settings, bot: Bot | None = None) -> None:
        self.settings = settings
        self.bot = bot
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    async def reply(self, user_text: str, language: str = "uz", user_context: str | None = None) -> str:
        if self._asks_for_signal(user_text):
            return self._signal_refusal(language)
        if not _is_trading_related(user_text):
            return _off_topic_reply(language)
        if self.client and self.settings.openai_text_active:
            prompt = (
                f"{IRON_AI_SYSTEM_PROMPT}\n\n"
                "Javob uslubi:\n"
                "- 3-7 qisqa blokdan oshirma.\n"
                "- Agar savol CPI, NFP, FOMC, GDP, inflation, interest rate, PMI kabi yangilik haqida bo‘lsa: nima ekanini, bozorga qanday ta’sir qilishini va risk qoidani tushuntir.\n"
                "- Agar user yangilik tahlilini xohlasa, yangilik matni yoki screenshotini yuborishni so‘ra.\n"
                "- Agar savol indikator haqida bo‘lsa: vazifasi, xato ishlatilishi, to‘g‘ri ishlatish qoidasi bilan javob ber.\n\n"
                f"User konteksti:\n{user_context or 'Ma’lumot yo‘q'}\n\n"
                f"User savoli:\n{user_text}"
            )
            text = await self._call_text_model(prompt, max_tokens=900)
            if text:
                return text
        return self._fallback_reply(user_text, language, user_context)

    async def extract_journal(self, user_text: str, trading_type: str | None = None) -> dict[str, Any]:
        if self.client and self.settings.openai_text_active:
            prompt = f"{JOURNAL_EXTRACTION_PROMPT}\n\nKnown trading_type: {trading_type or 'null'}\nUser text:\n{user_text}"
            text = await self._call_text_model(prompt, max_tokens=1200)
            parsed = _loads_json(text)
            if parsed:
                return _normalize_extraction(parsed, user_text, trading_type)
        return fallback_extract_journal(user_text, trading_type)

    async def organize_strategy(self, strategy_text: str, trading_type: str | None = None) -> dict[str, Any]:
        fallback = fallback_strategy(strategy_text, trading_type)
        if self.client and self.settings.openai_text_active:
            prompt = (
                "Quyidagi trading strategiyani tartiblangan JSONga ajrat. "
                "O‘ylab topma. JSON keys: trading_style, timeframe, instruments, risk_preference, "
                "market_type, leverage_usage, clean_strategy_text. Faqat JSON qaytar.\n\n"
                f"Trading type: {trading_type}\nStrategy:\n{strategy_text}"
            )
            text = await self._call_text_model(prompt, max_tokens=800)
            parsed = _loads_json(text)
            if parsed:
                fallback.update({key: value for key, value in parsed.items() if value not in (None, "", [])})
        return fallback

    async def _call_text_model(self, prompt: str, max_tokens: int = 900) -> str | None:
        if not self.client:
            return None
        for model in self.settings.openai_model_candidates(self.settings.resolved_openai_text_model):
            try:
                response = await self.client.responses.create(
                    model=model,
                    input=prompt,
                    temperature=self.settings.openai_temperature,
                    max_output_tokens=max_tokens,
                )
                text = (response.output_text or "").strip()
                if text:
                    return text
            except Exception as exc:
                await self._notify_openai_problem(exc, model)
                continue
        return None

    async def _notify_openai_problem(self, exc: Exception, model: str | None) -> None:
        key = openai_problem_key(exc)
        if not key:
            return
        await notify_admins(
            self.bot,
            self.settings,
            key,
            openai_alert_text(key.replace("openai_", ""), model),
        )

    @staticmethod
    def _asks_for_signal(text: str) -> bool:
        lower = (text or "").lower()
        signal_words = ("buy qilaymi", "sell qilaymi", "buy or sell", "signal ber", "точный сигнал", "should i buy", "should i sell")
        return any(word in lower for word in signal_words)

    @staticmethod
    def _signal_refusal(language: str) -> str:
        if language == "ru":
            return "Do‘stim, aniq buy/sell signal bera olmayman. Lekin risk, reja, entry sababingiz va jurnal natijalaringizni tahlil qilib beraman. Это не финансовая рекомендация."
        if language == "en":
            return "Friend, I cannot give a direct buy/sell signal. I can help review your plan, risk, entry reason and journal stats. This is not financial advice."
        return "Do‘stim, aniq buy/sell signal bera olmayman. Lekin reja, risk, entry sababi va jurnal natijalaringizni tahlil qilib beraman. Bu moliyaviy maslahat emas."

    @staticmethod
    def _fallback_reply(user_text: str, language: str, user_context: str | None = None) -> str:
        lower = (user_text or "").lower()
        disclaimer = {"uz": DISCLAIMER_UZ, "ru": DISCLAIMER_RU, "en": DISCLAIMER_EN}.get(language, DISCLAIMER_UZ)
        context_line = f"\n\n📊 Jurnal konteksti: {user_context}" if user_context else ""
        if any(word in lower for word in ("risk", "lot", "deposit", "depozit", "stop", "sl")):
            return (
                "🤖 Iron AI:\n\n"
                "Do‘stim, riskni birinchi o‘ringa qo‘ying: bitta savdoda yo‘qotishga tayyor summani oldindan yozing. "
                "Xato: lotni foyda istagiga qarab tanlash. Yechim: stop-loss masofasi va depositga nisbatan risk foizi bilan hisoblash."
                f"{context_line}\n\n{disclaimer}"
            )
        if any(word in lower for word in ("cpi", "inflation", "inflyatsiya", "инфляц")):
            return (
                "🤖 Iron AI:\n\n"
                "<b>CPI</b> — Consumer Price Index, ya’ni iste’mol narxlari indeksi. U inflyatsiya qanchalik tez o‘sayotganini ko‘rsatadi.\n\n"
                "📌 Tradingga ta’siri:\n"
                "• CPI kutilgandan yuqori chiqsa, USD kuchayishi va risk assetlarga bosim bo‘lishi mumkin.\n"
                "• CPI past chiqsa, bozor Fed yumshashi mumkin deb o‘ylashi mumkin.\n"
                "• XAUUSD, indekslar, crypto va major FX paralar kuchli volatil bo‘ladi.\n\n"
                "⚠️ Xato: yangilik chiqqan birinchi sekundlarda rejasiz kirish.\n"
                "✅ Yechim: avval spread, volatility va risk limitni tekshirish.\n\n"
                "Agar CPI yangiligi bo‘lsa, matnini yoki screenshotini yuboring, birgalikda tahlil qilib ko‘ramiz.\n\n"
                f"{disclaimer}"
            )
        if any(word in lower for word in ("nfp", "fomc", "pmi", "gdp", "interest rate", "stavka", "fed", "ecb", "boe", "boj", "unemployment", "retail sales", "fundamental", "yangilik", "news")):
            return (
                "🤖 Iron AI:\n\n"
                "Do‘stim, bu fundamental/news mavzusi. Bunday yangiliklarda 3 narsa muhim: <b>kutilgan qiymat</b>, <b>real natija</b> va <b>bozor reaksiyasi</b>.\n\n"
                "Sabab: narx faqat raqamga emas, raqamning kutilmaga nisbatan farqiga javob beradi.\n"
                "Xato: headline ko‘rib darhol trade qilish.\n"
                "Yechim: yangilik matni, forecast/actual/previous va qaysi instrumentni kuzatayotganingizni yuboring.\n\n"
                "Yangilikni menga yuboring, birgalikda risk va ehtimoliy ta’sirini tahlil qilamiz.\n\n"
                f"{disclaimer}"
            )
        if any(word in lower for word in ("rsi", "macd", "ema", "sma", "bollinger", "atr", "ichimoku", "indicator", "indikator")):
            return (
                "🤖 Iron AI:\n\n"
                "Indikatorlar narxni oldindan bilmaydi, ular narxdagi holatni tartibli ko‘rsatadi.\n\n"
                "Sabab: RSI/MACD/EMA trend, momentum yoki volatilityni o‘lchaydi.\n"
                "Xato: bitta indikator signalini alohida trade sababi qilish.\n"
                "Yechim: indikatorni trend, support/resistance, session va risk-reward bilan birga ishlating.\n\n"
                "Qaysi indikatorni ishlatyapsiz? Screenshot yuborsangiz, sozlamasi va xatolarini ko‘rib beraman.\n\n"
                f"{disclaimer}"
            )
        if any(word in lower for word in ("overtrade", "overtrading", "zarar", "loss", "revenge", "shoshil")):
            return (
                "🤖 Iron AI:\n\n"
                "Do‘stim, zarar ko‘payishining eng ko‘p sababi strategiya emas, intizom buzilishi bo‘ladi. "
                "Sabab: profit yoki lossdan keyin qayta kirish. Xato: entry sababini yozmasdan savdo qilish. "
                "Yechim: 2 ta zararli savdodan keyin savdoni to‘xtatish qoidasi."
                f"{context_line}\n\n{disclaimer}"
            )
        if any(word in lower for word in ("smc", "ict", "fvg", "order block", "support", "resistance")):
            return (
                "🤖 Iron AI:\n\n"
                "Do‘stim, SMC/ICT’da avval trend va liquidity zonani belgilang, keyin entry uchun tasdiq kuting. "
                "Xato: faqat bitta FVG yoki order block ko‘rib shoshilish. Yechim: risk-reward, session va stop joyini oldindan yozish."
                f"{context_line}\n\n{disclaimer}"
            )
        return (
            "🤖 Iron AI:\n\n"
            "Do‘stim, savolingizni tushundim. Aniqroq tahlil uchun jurnalga instrument, risk %, natija va emotionni yozib boring. "
            "Men sizga sabab → xato → yechim shaklida yordam beraman."
            f"{context_line}\n\n{disclaimer}"
        )


def fallback_extract_journal(user_text: str, trading_type: str | None = None) -> dict[str, Any]:
    raw = user_text or ""
    lower = raw.lower()
    detected_type = trading_type or ("crypto" if any(w in lower for w in ("btc", "eth", "sol", "crypto", "coin", "futures", "spot")) else "forex")
    instrument = _detect_instrument(raw, detected_type)
    risk = _first_number_after(raw, ("risk", "riskim", "риск"))
    trade_count = _trade_count(raw)
    profit_amount, loss_amount, net_result = _money_result(raw)
    result_type = "profit" if net_result > 0 else "loss" if net_result < 0 else "breakeven" if "0" in raw else None
    emotion = _detect_emotion(lower)
    session = _detect_session(lower)
    timeframe = _detect_timeframe(raw)
    missing: list[str] = []
    if not instrument:
        missing.append("instrument")
    if risk is None:
        missing.append("risk_percent")
    if result_type is None:
        missing.append("result_type")
    summary = _summary_from_result(net_result, emotion)
    return {
        "trading_type": detected_type,
        "date": str(date.today()),
        "instrument": instrument,
        "pair": instrument if detected_type == "forex" else None,
        "coin_symbol": instrument if detected_type == "crypto" else None,
        "market_type": "futures" if "futures" in lower else "spot" if "spot" in lower else None,
        "session": session,
        "timeframe": timeframe,
        "trade_count": trade_count,
        "entry_reason": _entry_reason(raw),
        "risk_percent": risk,
        "profit_amount": profit_amount,
        "loss_amount": loss_amount,
        "net_result": net_result,
        "result_type": result_type,
        "emotion": emotion,
        "mistakes": _detect_mistakes(lower),
        "good_decisions": _detect_good_decisions(lower),
        "missing_fields": missing,
        "summary": summary,
        "raw_text": raw,
    }


def fallback_strategy(strategy_text: str, trading_type: str | None = None) -> dict[str, Any]:
    raw = strategy_text or ""
    lower = raw.lower()
    instruments = sorted(set(re.findall(r"\b(XAUUSD|EURUSD|GBPUSD|USDJPY|GBPJPY|NAS100|US30|BTC|ETH|SOL|BNB|XRP)\b", raw.upper())))
    timeframe = ", ".join(sorted(set(re.findall(r"\b(?:M\d+|H\d+|D1|W1|\d+\s?(?:m|h|d))\b", raw, re.I)))) or None
    style = None
    for key in ("smc", "ict", "price action", "indicator", "news"):
        if key in lower:
            style = key.upper() if key in {"smc", "ict"} else key.title()
            break
    risk = None
    match = re.search(r"risk\D{0,10}(\d+(?:[.,]\d+)?)\s?%", lower)
    if match:
        risk = f"{match.group(1).replace(',', '.')}%"
    return {
        "trading_style": style,
        "timeframe": timeframe,
        "instruments": instruments,
        "risk_preference": risk,
        "market_type": "futures" if "futures" in lower else "spot" if "spot" in lower else trading_type,
        "leverage_usage": _leverage(raw),
        "clean_strategy_text": raw.strip(),
    }


def _normalize_extraction(data: dict[str, Any], raw_text: str, trading_type: str | None) -> dict[str, Any]:
    data.setdefault("trading_type", trading_type)
    data.setdefault("date", str(date.today()))
    data.setdefault("missing_fields", [])
    data.setdefault("mistakes", [])
    data.setdefault("good_decisions", [])
    data["raw_text"] = raw_text
    if data.get("date") in (None, "null"):
        data["date"] = str(date.today())
    if data.get("net_result") is None:
        data["net_result"] = float(data.get("profit_amount") or 0) - float(data.get("loss_amount") or 0)
    if not data.get("instrument"):
        data["instrument"] = data.get("pair") or data.get("coin_symbol")
    if data.get("trading_type") is None:
        data["trading_type"] = trading_type
    missing = set(data.get("missing_fields") or [])
    for field in ("instrument", "risk_percent", "result_type"):
        if not data.get(field):
            missing.add(field)
    data["missing_fields"] = sorted(missing)
    return data


def _loads_json(text: str | None) -> dict[str, Any] | None:
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        data = json.loads(cleaned)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.S)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            return None


def _detect_instrument(text: str, trading_type: str) -> str | None:
    upper = text.upper()
    if trading_type == "crypto":
        match = re.search(r"\b(BTC|ETH|SOL|BNB|XRP|ADA|DOGE|TON|AVAX)(?:USDT|USD)?\b", upper)
        return match.group(1) if match else None
    match = re.search(r"\b(XAUUSD|EURUSD|GBPUSD|USDJPY|GBPJPY|NAS100|US30|AUDUSD|USDCAD|USDCHF|NZDUSD)\b", upper)
    return match.group(1) if match else None


def _first_number_after(text: str, labels: tuple[str, ...]) -> float | None:
    lower = text.lower()
    for label in labels:
        match = re.search(rf"{re.escape(label)}\D{{0,12}}(\d+(?:[.,]\d+)?)\s?%?", lower)
        if match:
            return float(match.group(1).replace(",", "."))
    match = re.search(r"(\d+(?:[.,]\d+)?)\s?%\s*(?:risk|xavf)?", lower)
    return float(match.group(1).replace(",", ".")) if match else None


def _trade_count(text: str) -> int | None:
    match = re.search(r"(\d+)\s*(?:ta\s*)?(?:savdo|trade|trades)", text.lower())
    return int(match.group(1)) if match else None


def _money_result(text: str) -> tuple[float, float, float]:
    lower = text.lower()
    signed = re.findall(r"([+-]\s?\d+(?:[.,]\d+)?)\s?\$?", text)
    if signed:
        net = sum(float(value.replace(" ", "").replace(",", ".")) for value in signed)
        return (net if net > 0 else 0.0, abs(net) if net < 0 else 0.0, net)
    profit = _number_near(lower, ("profit", "foyda", "plus"))
    loss = _number_near(lower, ("loss", "zarar", "minus"))
    profit = float(profit or 0)
    loss = float(loss or 0)
    return profit, loss, profit - loss


def _number_near(text: str, labels: tuple[str, ...]) -> float | None:
    for label in labels:
        match = re.search(rf"{label}\D{{0,12}}(\d+(?:[.,]\d+)?)", text)
        if match:
            return float(match.group(1).replace(",", "."))
    return None


def _is_trading_related(text: str) -> bool:
    lower = (text or "").lower()
    if len(lower.strip()) <= 3 and lower.strip() in {"hi", "hey", "salom", "пр"}:
        return False
    keywords = (
        "trade", "trading", "trader", "forex", "crypto", "kript", "invest", "investitsiya", "portfolio",
        "risk", "lot", "leverage", "margin", "deposit", "stop", "stop loss", "take profit", "profit", "loss",
        "xau", "gold", "oltin", "eurusd", "gbpusd", "usdjpy", "nas100", "us30", "sp500", "s&p", "dow", "dax",
        "btc", "bitcoin", "eth", "ethereum", "sol", "coin", "futures", "spot",
        "indicator", "indikator", "rsi", "macd", "ema", "sma", "ma ", "bollinger", "atr", "volume", "vwap",
        "support", "resistance", "trend", "liquidity", "smc", "ict", "fvg", "order block", "price action",
        "fundamental", "news", "yangilik", "iqtisod", "economic", "economy", "macro", "makro",
        "cpi", "ppi", "nfp", "fomc", "fed", "ecb", "boe", "boj", "interest", "rate", "stavka", "inflation",
        "inflyatsiya", "gdp", "pmi", "unemployment", "retail sales", "yield", "bond", "dxy", "dollar",
        "aksiy", "stock", "share", "etf", "dividend", "valuation", "index", "indeks",
        "savdo", "bozor", "narx", "chart", "grafik", "svecha", "candlestick", "session", "sessiya",
        "трейд", "форекс", "крипто", "инвест", "риск", "индикатор", "новост", "инфляц", "ставк",
    )
    return any(keyword in lower for keyword in keywords)


def _off_topic_reply(language: str) -> str:
    if language == "en":
        return (
            "🤖 Iron AI:\n\n"
            "Friend, I am focused on trading, investing, risk, journals, indicators and market analysis.\n\n"
            "I can help you with:\n"
            "📘 trade journaling\n📊 statistics\n🧠 strategy review\n🧮 risk calculation\n"
            "📈 instrument rating\n📰 economic news analysis\n📄 PDF/Excel reports\n\n"
            "Send me a trade, chart screenshot, news text, or a trading question."
        )
    if language == "ru":
        return (
            "🤖 Iron AI:\n\n"
            "Друг, я специализируюсь на трейдинге, инвестициях, риске, журнале, индикаторах и анализе рынка.\n\n"
            "Я могу помочь с:\n"
            "📘 торговым журналом\n📊 статистикой\n🧠 анализом стратегии\n🧮 risk calculator\n"
            "📈 рейтингом инструментов\n📰 анализом экономических новостей\n📄 PDF/Excel отчётами\n\n"
            "Отправьте сделку, скриншот графика, текст новости или вопрос по трейдингу."
        )
    return (
        "🤖 Iron AI:\n\n"
        "Do‘stim, men trading, investitsiya, risk, jurnal, indikator va bozor tahliliga ixtisoslashganman.\n\n"
        "Men sizga shu ishlarda yordam beraman:\n"
        "📘 savdolarni jurnalga yozish\n"
        "📊 statistika chiqarish\n"
        "🧠 strategiyani tahlil qilish\n"
        "🧮 riskni hisoblash\n"
        "📈 qaysi instrument mosligini ko‘rsatish\n"
        "📰 iqtisodiy yangiliklarni tahlil qilish\n"
        "📄 PDF/Excel hisobot tayyorlash\n\n"
        "Savdo natijangizni, chart screenshotni, yangilik matnini yoki trading savolingizni yuboring."
    )


def _detect_emotion(lower: str) -> str | None:
    mapping = {
        "calm": ("tinch", "calm", "xotirjam"),
        "fear": ("qo‘rq", "qorq", "fear", "scared"),
        "revenge": ("revenge", "alam", "qasd"),
        "rush": ("shosh", "rush", "tez kirdim"),
        "greed": ("ochko‘z", "ochkoz", "greed"),
        "normal": ("oddiy", "normal"),
    }
    for emotion, words in mapping.items():
        if any(word in lower for word in words):
            return emotion
    return None


def _detect_session(lower: str) -> str | None:
    if "london" in lower:
        return "london"
    if "new york" in lower or "ny" in lower:
        return "new_york"
    if "asia" in lower or "osiyo" in lower:
        return "asia"
    return None


def _detect_timeframe(text: str) -> str | None:
    match = re.search(r"\b(M\d+|H\d+|D1|W1|\d+\s?(?:m|h|d))\b", text, re.I)
    return match.group(1).replace(" ", "") if match else None


def _entry_reason(text: str) -> str | None:
    cleaned = text.strip()
    return cleaned[:500] if cleaned else None


def _detect_mistakes(lower: str) -> list[str]:
    mistakes = []
    if "shosh" in lower or "rush" in lower:
        mistakes.append("Shoshilib entry qilish")
    if "revenge" in lower:
        mistakes.append("Revenge trade")
    if "sl" in lower and ("yo'q" in lower or "yoq" in lower):
        mistakes.append("Stop-loss rejasi noaniq")
    return mistakes


def _detect_good_decisions(lower: str) -> list[str]:
    good = []
    if "sl" in lower or "stop" in lower:
        good.append("Stop-loss haqida o‘ylangan")
    if "reja" in lower or "plan" in lower:
        good.append("Reja bilan savdo qilingan")
    return good


def _summary_from_result(net_result: float, emotion: str | None) -> str:
    if net_result > 0:
        return "Savdo foyda bilan yopilgan. Keyingi safar exit rejani ham oldindan yozing."
    if net_result < 0:
        note = " Emotion ta’siri bor ko‘rinadi." if emotion in {"rush", "revenge", "fear", "greed"} else ""
        return f"Zararli savdo. Sababni entrydan oldin yozish va riskni cheklash muhim.{note}"
    return "Natija neytral yoki aniqlanmagan. Jurnal ma’lumotlarini to‘liqroq yozing."


def _leverage(text: str) -> str | None:
    match = re.search(r"\b(\d{1,3})\s?x\b", text.lower())
    return f"{match.group(1)}x" if match else None
