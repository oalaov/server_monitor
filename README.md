Python script for server monitoring with web interface and telegram control panel.

# Server Monitor

Система мониторинга сервера с веб-интерфейсом и Telegram-ботом.

**Стек:** Python, Flask, Bootstrap, SQLite, Docker, Telegram Bot API, psutil.

---

## Возможности

- 📊 Мониторинг CPU, RAM, диска в реальном времени
- 📈 Графики нагрузки (история до 20 точек)
- ⚠️ Логирование алертов в базу данных
- 🤖 Telegram-бот для удалённого управления и уведомлений
- 🔒 Блокировка и выключение сервера через бота
- 🐳 Готов к запуску в Docker

---

## Быстрый старт (Docker)

### 1. Клонируй репозиторий

```bash
git clone https://github.com/твой-username/server_monitor.git
cd server_monitor
```

### 2. В файле alerts.py замени токен бота и chat id на свой
```python
TOKEN = "8775232211:AAEXIUkYXDPzk1XkYRoT_6CKK48kxRJ2TAI"
CHAT_ID = "7926748416"
```

### 3. Запусти одной командой 
```bash
docker-compose up -d
```

### 4. Телеграм бот и веб
1. Открой своего бота и отправь /start
2. Открой в браузере
 
```bash
http://localhost:5000
