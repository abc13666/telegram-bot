"""
Telegram-бот для круглосуточной работы на Render.com (бесплатный тариф).

Особенности:
- Polling Telegram запускается в отдельном потоке (daemon).
- Параллельно Flask-сервер слушает порт и отвечает на health-check,
  чтобы Render считал сервис "живым".
- Токен читается из переменной окружения BOT_TOKEN (не хранится в коде!).
"""

import os
import threading

import telebot
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


# ------------------------- Хендлеры бота -------------------------

@bot.message_handler(commands=["start"])
def handle_start(message):
    """Отвечает на команду /start."""
    bot.reply_to(message, "Привет!")


@bot.message_handler(commands=["health"])
def handle_health(message):
    """Команда /health в чате — проверка, что бот жив."""
    bot.reply_to(message, "Я на связи! ✅")


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
    # Поток с ботом: daemon=True — он завершится вместе с основным процессом
    bot_thread = threading.Thread(target=run_bot_polling, daemon=True)
    bot_thread.start()

    # Flask обязан слушать порт — Render требует открытый порт для web-сервиса.
    # Render передаёт номер порта в переменной окружения PORT.
    port = int(os.environ.get("PORT", 5000))
    print(f"[WEB] Flask слушает порт {port}...", flush=True)
    app.run(host="0.0.0.0", port=port)

