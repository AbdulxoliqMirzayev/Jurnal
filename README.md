# Iron Trade

Iron Trade — AI asosidagi Telegram trading journal bot. Iron AI user savdolarini text, screenshot, risk, profit/loss, emotion va izohlar bilan jurnalga saqlaydi, statistikani chiqaradi, strategiyani tahlil qiladi, PDF/Excel hisobot tayyorlaydi va intizomni yaxshilashga yordam beradi.

Bot hech qachon aniq buy/sell signal bermaydi va moliyaviy maslahat bermaydi. Tahlillar faqat user jurnali va educational kontekstga asoslanadi.

## Features

- `/start` onboarding: til tanlash, Forex/Crypto, strategiya, deposit, risk
- Doimiy reply keyboard asosiy menyu
- AI chat fallback: user oddiy savol yozsa Iron AI javob beradi
- Trading journal text extraction: Forex/Crypto maydonlarini JSONga ajratish
- Screenshot `file_id` saqlash va optional Vision tahlil
- Emotion tracking va emotion bo‘yicha xulosalar
- Strategiya tahlili, statistika, instrument reytingi
- Risk kalkulyator
- Kunlik APScheduler eslatmalar
- PDF va Excel export
- Premium visual PDF: equity curve, instrument PnL, emotion chart, risk distribution
- Excel chart sheets: equity, instrument, emotion grafiklari
- OpenAI token/quota muammosida admin alert
- Polling default, Railway webhook optional
- Feedback va admin bilan bog‘lanish
- Admin panel, bot statistikasi va broadcast
- Sticker/animation file_id safe support
- Uzbek, English, Russian uchun config/locales tayyor

## Tech Stack

Python 3.11+, aiogram 3.x, PostgreSQL, SQLAlchemy async, Alembic, OpenAI API, openpyxl, reportlab, APScheduler, Docker, Railway.

## Installation

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` ichida kamida quyidagilarni to‘ldiring:

```env
BOT_TOKEN=<telegram-bot-token>
OPENAI_API_KEY=sk-...
```

Shu ikkitasi bilan bot SQLite orqali ishlaydi. Katta trafik/production uchun `DATABASE_URL` va `ADMIN_ID` ham qo‘ying.

## PostgreSQL Setup

```bash
createdb iron_trade
alembic upgrade head
```

Development uchun `DATABASE_URL` bo‘sh qoldirilsa SQLite ishlaydi:

```env
DATABASE_URL=
DB_PATH=data/iron_trade.db
```

Bot start paytida MVP qulayligi uchun SQLAlchemy `create_all` ham ishlaydi. Production’da Alembic migration ishlatish tavsiya qilinadi.

## Run Bot

```bash
source .venv/bin/activate
python run_bot.py
```

Alternative entrypoint:

```bash
python -m app.main
python main.py
```

## Docker Run

```bash
cp .env.example .env
docker compose up --build
```

Compose `postgres` va `bot` servicelarini ko‘taradi. Export fayllar `exports/` ichida yaratiladi.

## Railway Deploy

Railway variables:

- `BOT_TOKEN`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_VISION_MODEL`
- `DATABASE_URL` PostgreSQL ulanganda
- `ADMIN_ID` yoki `ADMIN_IDS`
- `ADMIN_USERNAME=mirzayev_ai`
- `DEFAULT_TIMEZONE=Asia/Tashkent`

Start command:

```bash
python -m app.main
```

Default polling rejimi ishlaydi. Webhook kerak bo‘lsa Railway public domain olgandan keyin:

```env
WEBHOOK_URL=https://your-app.up.railway.app
WEBHOOK_PATH=/webhook
WEBHOOK_SECRET=long-random-secret
```

Webhook ishlaganda app `0.0.0.0:$PORT` da health endpoint ham ochadi:

```text
/health
```

## Admin Setup

`.env`:

```env
ADMIN_IDS=123456789,987654321
ADMIN_USERNAME=mirzayev_ai
```

Admin command:

```text
/admin
```

Admin panel: bot statistikasi, OpenAI holati, broadcast preview, userlar, murojaatlar, exportlar.

## AI API Setup

```env
OPENAI_API_KEY=
OPENAI_TEXT_MODEL=gpt-5.5
OPENAI_VISION_MODEL=gpt-5.5
```

OpenAI API bo‘lmasa ham bot fallback parser va rule-based Iron AI javoblari bilan ishlaydi. Vision API bo‘lmasa screenshot `file_id` saqlanadi, lekin chart tahlil taxminiy fallback bo‘ladi.

## Sticker File ID Qo‘shish

`.env` ichida optional:

```env
ENABLE_STICKERS=true
ENABLE_ANIMATIONS=true
WELCOME_STICKER_ID=
JOURNAL_STICKER_ID=
SUCCESS_STICKER_ID=
WARNING_STICKER_ID=
PROFIT_STICKER_ID=
LOSS_STICKER_ID=
RISK_STICKER_ID=
STATS_STICKER_ID=
EXPORT_STICKER_ID=
REMINDER_STICKER_ID=
EMOTION_STICKER_ID=
ADMIN_STICKER_ID=
WELCOME_ANIMATION_ID=
JOURNAL_ANIMATION_ID=
WRITING_ANIMATION_ID=
```

File ID bo‘lmasa bot xato bermaydi, emoji/text bilan ishlayveradi.

## Export Setup

PDF export uchun `reportlab`, Excel uchun `openpyxl` ishlatiladi. Fayllar Telegramga document sifatida yuboriladi va `exports/` papkasida saqlanadi.

PDF ichida:

- Discipline score
- Summary cards
- Equity curve
- Instrument PnL chart
- Emotion pie chart
- Risk distribution
- GPT/AI action plan
- Trade list
- Disclaimer

Excel sheetlar:

1. Summary
2. Trades
3. Instruments
4. Emotions
5. Deposit History
6. AI Notes
7. Charts

## Project Structure

```text
app/
  main.py
  config.py
  bot/
    handlers/
    keyboards/
    middlewares/
  services/
  database/
    models.py
    session.py
    repositories/
  locales/
  utils/
alembic/
exports/
Dockerfile
docker-compose.yml
```

## Verification

```bash
python -m compileall app
python -m pytest -q
DATABASE_URL=sqlite+aiosqlite:////tmp/iron_trade.db alembic upgrade head
```
