"""
Telegram-бот для круглосуточной работы на Render.com (бесплатный тариф).

Особенности:
- Polling Telegram запускается в отдельном потоке (daemon).
- Параллельно Flask-сервер слушает порт и отвечает на health-check,
  чтобы Render считал сервис "живым".
- Каждый день в 08:00 (Europe/Moscow) планировщик APScheduler отправляет
  случайное романтичное сообщение всем подписчикам (файл subscribers.txt).
- Токен читается из переменной окружения BOT_TOKEN (не хранится в коде!).
"""

import os
import random
import threading

import telebot
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask

# ============================================================
# Токен берётся из переменной окружения BOT_TOKEN.
# Локально (PowerShell):      $env:BOT_TOKEN="ваш_токен"
# На Render.com:              Environment -> BOT_TOKEN
# ============================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

if not BOT_TOKEN:
    raise SystemExit(
        "ОШИБКА: не задана переменная окружения BOT_TOKEN!\n"
        "Локально в PowerShell выполните:  $env:BOT_TOKEN=\"ваш_токен\"\n"
        "На Render.com добавьте её в Environment Variables."
    )

bot = telebot.TeleBot(BOT_TOKEN)

# Файл, в который сохраняются chat_id подписчиков (по команде /start)
SUBSCRIBERS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "subscribers.txt"
)

# ------------------- Утренние сообщения для Насти -------------------

MORNING_MESSAGES = [
    "Доброе утро, Настюша! Ты самая прекрасная девушка в этом мире. "
    "Я тебя очень сильно люблю ❤️",

    "Доброе утро, моя любимая! Пусть этот день будет таким же чудесным, "
    "как твоя улыбка 😘",

    "С добрым утром, Настенька! Просыпайся солнышком — сегодня мир снова "
    "будет немного лучше, потому что в нём есть ты ☀️",

    "Доброе утро, моё счастье! Спасибо, что ты есть: с тобой каждое утро "
    "добрее, а каждый день светлее 💖",

    "Просыпайся, красавица! Сегодня отличный день, чтобы покорить мир — "
    "а я всегда рядом, чтобы поддержать 🌸",

    "Доброе утро, Настюша! Знаешь, что я подумал первым делом сегодня? "
    "О тебе. Как и всегда 💭❤️",

    "С добрым утром, любимая! Пусть кофе будет крепким, настроение — "
    "прекрасным, а вечером я расскажу, как сильно по тебе скучал ☕💕",
]

# ---------------------- Подписчики (subscribers) ----------------------

def load_subscribers():
    """Читает список chat_id из файла subscribers.txt."""
    try:
        with open(SUBSCRIBERS_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []


def save_subscriber(chat_id):
    """Добавляет chat_id в subscribers.txt (без дубликатов)."""
    subscribers = load_subscribers()
    chat_id = str(chat_id)
    if chat_id not in subscribers:
        subscribers.append(chat_id)
        with open(SUBSCRIBERS_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(subscribers))
        print(f"[SUBS] Новый подписчик: {chat_id}", flush=True)


# ------------------------- Хендлеры бота -------------------------

@bot.message_handler(commands=["start"])
def handle_start(message):
    """Приветствует пользователя и подписывает на утренние сообщения."""
    save_subscriber(message.chat.id)
    bot.reply_to(
        message,
        "Привет! Теперь я буду присылать тебе доброе утро "
        "каждый день в 08:00 💕",
    )


@bot.message_handler(commands=["health"])
def handle_health(message):
    """Команда /health в чате — проверка, что бот жив."""
    bot.reply_to(message, "Я на связи! ✅")


# ------------------- Утренняя рассылка (APScheduler) -------------------

def send_morning_message():
    """Выбирает случайное сообщение и отправляет всем подписчикам."""
    subscribers = load_subscribers()
    if not subscribers:
        print("[SCHEDULER] Нет подписчиков — некому отправлять", flush=True)
        return

    text = random.choice(MORNING_MESSAGES)
    for chat_id in subscribers:
        try:
            bot.send_message(chat_id, text)
            print(f"[SCHEDULER] Отправлено: {chat_id}", flush=True)
        except Exception as e:
            print(f"[SCHEDULER] Ошибка отправки {chat_id}: {e}", flush=True)


def start_scheduler():
    """Запускает планировщик: каждый день в 08:00 по Москве."""
    scheduler = BackgroundScheduler(timezone="Europe/Moscow")
    scheduler.add_job(
        send_morning_message,
        CronTrigger(hour=8, minute=0, timezone="Europe/Moscow"),
        id="morning_message",
        # если сервис "проспал" момент отправки — отправит в течение часа
        misfire_grace_time=3600,
    )
    scheduler.start()
    print("[SCHEDULER] Запущен: ежедневно в 08:00 (Europe/Moscow)", flush=True)


# --------------------- Flask-сервер (health-check) ---------------------

app = Flask(__name__)


@app.route("/")
def index():
    """Главная страница — по ней будет пинговать UptimeRobot."""
    return "Бот работает! ✅"


@app.route("/health")
def health():
    """Health-check эндпоинт для Render."""
    return {"status": "ok"}, 200


# --------------------------- Запуск ---------------------------

def run_bot_polling():
    """Бесконечный polling Telegram в отдельном потоке."""
    print("[BOT] Polling запущен...", flush=True)
    # infinity_polling сам переподключается при ошибках сети
    bot.infinity_polling(timeout=60, long_polling_timeout=60)


if __name__ == "__main__":
    # 1. Планировщик утренних сообщений (08:00 Europe/Moscow)
    start_scheduler()

    # 2. Поток с ботом: daemon=True — завершится вместе с процессом
    bot_thread = threading.Thread(target=run_bot_polling, daemon=True)
    bot_thread.start()

    # Flask обязан слушать порт — Render требует открытый порт для web-сервиса.
    # Render передаёт номер порта в переменной окружения PORT.
    port = int(os.environ.get("PORT", 5000))
    print(f"[WEB] Flask слушает порт {port}...", flush=True)
    app.run(host="0.0.0.0", port=port)

