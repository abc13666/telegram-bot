# Telegram-бот "Привет!" — круглосуточная работа на Render.com (бесплатно)

Бот отвечает "Привет!" на команду /start и работает 24/7 на бесплатном
тарифе Render.com. Чтобы бесплатный сервис не "засыпал" (Render усыпляет
его через 15 минут без трафика), бот одновременно:

1. Запускает **polling Telegram** в отдельном потоке;
2. Держит открытым **Flask-веб-сервер** (порт задаёт Render) — по нему
   сервис пингует UptimeRobot каждые 5 минут, имитируя трафик.

## Структура проекта

```
telegram_bot/
├── bot.py            — код бота (Flask + polling в потоке)
├── requirements.txt  — зависимости (pyTelegramBotAPI, Flask)
├── .gitignore        — что не загружать на GitHub
└── README.md         — этот файл
```

---

# ИНСТРУКЦИЯ: деплой с нуля (для новичка)

## Часть 1. Создание бота в BotFather (если ещё не сделано)

1. В Telegram найдите **@BotFather** → отправьте `/newbot`.
2. Задайте имя и username (заканчивается на `bot`).
3. Скопируйте **токен** вида `1234567890:AAE...` — он понадобится в части 4.

## Часть 2. Загрузка кода на GitHub

1. Зарегистрируйтесь на **github.com** (если аккаунта нет).
2. Нажмите **+** (правый верхний угол) → **New repository**.
3. Имя: например `telegram-bot`. Репозиторий можно сделать **Private** —
   Render работает и с приватными репозиториями. Нажмите **Create repository**.
4. Откройте терминал **в папке проекта** и выполните:

   ```powershell
   cd c:\OTHER\SYSTEM\telegram_bot

   git init
   git add .
   git commit -m "Telegram bot with health-check"
   git branch -M main
   git remote add origin https://github.com/ВАШ_ЛОГИН/telegram-bot.git
   git push -u origin main
   ```

   При первом push GitHub спросит логин и пароль — вместо пароля нужен
   **Personal Access Token** (GitHub → Settings → Developer settings →
   Personal access tokens → Generate new token, галочка `repo`).
   
   💡 Проще всего установить **GitHub Desktop** или войти через
   `git credential manager` — тогда авторизация пройдёт через браузер.

## Часть 3. Регистрация на Render.com и создание сервиса

1. Зайдите на **render.com** → **Get Started** → войдите через GitHub-аккаунт.
2. В панели нажмите **New +** → **Web Service**.
3. Выберите ваш репозиторий `telegram-bot` → **Connect**.
4. Заполните форму:
   - **Name**: `telegram-bot` (любое имя, оно войдёт в URL сервиса)
   - **Region**: Frankfurt (EU) — ближе к России, меньше пинг
   - **Branch**: `main`
   - **Runtime**: Python 3 (Render определит автоматически)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
   - **Instance Type**: **Free**
5. Прокрутите до **Environment Variables** и добавьте:

   | Key         | Value                                    |
   |-------------|------------------------------------------|
   | `BOT_TOKEN` | ваш токен от BotFather (`123456:AAE...`) |

6. Нажмите **Create Web Service** и подождите 3–5 минут, пока соберётся.
7. Вверху появится URL вида `https://telegram-bot-xxxx.onrender.com`.
   Откройте его в браузере — должно быть "Бот работает! ✅".
8. Отправьте боту в Telegram команду `/start` — он ответит "Привет!".

## Часть 4. UptimeRobot — чтобы бот не засыпал

Render Free усыпляет сервис через 15 минут без HTTP-запросов.
UptimeRobot будет пинговать наш URL каждые 5 минут — сервис не заснёт.

1. Зарегистрируйтесь на **uptimerobot.com** (бесплатно, до 50 мониторов).
2. Нажмите **Add New Monitor**.
3. Настройки:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: `Telegram Bot`
   - **URL**: `https://telegram-bot-xxxx.onrender.com/` (ваш URL с Render)
   - **Monitoring Interval**: `5 minutes`
4. Нажмите **Create Monitor**. Готово!

Теперь бот работает круглосуточно. Проверка: команда `/health` в чате —
бот ответит "Я на связи! ✅".

## Локальный запуск (для тестов)

```powershell
cd c:\OTHER\SYSTEM\telegram_bot
$env:BOT_TOKEN="ваш_токен"
python bot.py
```

Бот запустит polling на порту 5000: http://localhost:5000

---

## ⚠️ Важно про безопасность

- Токен хранится **только** в переменных окружения, в коде его нет.
- Если токен случайно попал в GitHub — перевыпустите его:
  BotFather → `/mybots` → выбрать бота → API Token → **Revoke**.
- Один Telegram-токен = один запущенный процесс бота. Если бот запущен
  и локально, и на Render — появится конфликт (409 Conflict). Останавливайте
  локальную копию перед деплоем.

## Полезные ссылки

- Render Dashboard: https://dashboard.render.com
- Логи сервиса: Render → ваш сервис → вкладка **Logs** (там видно,
  что polling запущен и Flask слушает порт)
- UptimeRobot: https://uptimerobot.com

