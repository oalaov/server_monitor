# Server Monitor

![Click here to see the Russian version](README_RU.md)

A server monitoring system with a web interface and Telegram bot.
---
![Monitoring Dashboard](screenshots/web_screenshot.png)

*Web interface with CPU/RAM/Disk graphs*

## Features

 - Real-time monitoring of CPU, RAM, and disk
 - Load graphs (history up to 20 points)
 - Alert logging to database
 - Telegram bot for remote management and notifications
 - Ready to run in Docker

 ---
<details>
<summary> Quick Start (Docker) </summary>

### 1. Clone the repository

 ```bash
 git clone https://github.com/oalaov/server_monitor.git && cd server_monitor
 ```

### 2. Create a .env file with the text below and replace the bot token, chat id, web username and password with your own
 ```bash
 TELEGRAM_BOT_TOKEN=ТВОЙ:ТОКЕН
 CHAT_ID=ТВОЙCHATID
 ADMIN_USERNAME=ИМЯ_ПОЛЬЗОВАТЕЛЯ
 ADMIN_PASSWORD=ПАРОЛЬ
 ```

### 3. Install Docker

- Windows: https://docs.docker.com/desktop/setup/install/windows-install/
- macOS: https://docs.docker.com/desktop/setup/install/mac-install/
- Linux: https://docs.docker.com/desktop/setup/install/linux/

### 4. Install node exporter

 - Windows: https://github.com/prometheus-community/windows_exporter
 - Linux/macOS https://prometheus.io/download/#node_exporter 


### 5. Run with a single command
 ```bash
 docker-compose up -d
 ```

### 6. Telegram bot and web interface
 1. Open your bot and send /start
 2. Open this in your browser:
 ```bash
 http://localhost:5000