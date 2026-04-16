

# Server Monitor

Система мониторинга сервера с веб-интерфейсом и Telegram-ботом.
---

## Возможности

 - Мониторинг CPU, RAM, диска в реальном времени
 - Графики нагрузки (история до 20 точек)
 - Логирование алертов в базу данных
 - Telegram-бот для удалённого управления и уведомлений
 - Готов к запуску в Docker

 ---

## Быстрый старт (Docker)

### 1. Клонируй репозиторий

 ```bash
 git clone https://github.com/твой-username/server_monitor.git && cd server_monitor
 ```

### 2. Создай файл .env с текстом ниже и замени токен бота и chat id на свой
 ```bash
 TELEGRAM_BOT_TOKEN=ТВОЙ:ТОКЕН
 CHAT_ID=ТВОЙCHATID
 ```

### 3. Установи node exporter 

 Windows: https://github.com/prometheus-community/windows_exporter
 Linux/macOS https://prometheus.io/download/#node_exporter 


### 4. Запусти одной командой 
 ```bash
 docker-compose up -d
 ```

### 5. Телеграм бот и веб
 1. Открой своего бота и отправь /start
 2. Открой в браузере
 
 ```bash
 http://localhost:5000
