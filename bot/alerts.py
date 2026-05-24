import telebot
import time
import psutil
import threading
import os
import requests
from telebot import types

# TOKEN AND CHAT ID
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID", "7926748416"))

WEB_URL = os.getenv("WEB_URL", "http://web:5000")

bot = telebot.TeleBot(TOKEN)
last_alert_time = 0


def get_metrics():
    """Получить метрики из Flask-приложения. Fallback — psutil."""
    try:
        resp = requests.get(f"{WEB_URL}/api/metrics", timeout=3)
        data = resp.json()
        return data['cpu'], data['ram'], data['disk']
    except Exception as e:
        print(f"⚠️ Flask недоступен, берём из psutil: {e}")
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        return cpu, ram, disk


def send_notification(message):
    global last_alert_time
    current_time = time.time()

    if current_time - last_alert_time > 10:
        try:
            bot.send_message(CHAT_ID, message)
            last_alert_time = current_time
            print("Алерт отправлен в Telegram")
        except Exception as e:
            print(f"Ошибка бота при отправке: {e}")
    else:
        print("Алерт пропущен (защита от спама)")


def get_menu_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Пока не работает :)", callback_data="menu_firstButton"))
    return markup


def get_hardware_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Полные данные", callback_data="get_hardware"))
    return markup


def get_inline_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Да, выключай", callback_data="confirm_shutdown"),
        types.InlineKeyboardButton("Нет, отмена", callback_data="cancel")
    )
    return markup


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    if call.data == "get_hardware":
        cpu, ram, disk = get_metrics()
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"📊 Полные данные:\nCPU: {cpu}%\nRAM: {ram}%\nDisk: {disk}%"
        )

    elif call.data == "menu_firstButton":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Пока не работает :)"
        )

    elif call.data == "confirm_shutdown":
        bot.answer_callback_query(call.id, text="Выполняю!")
        bot.send_message(call.message.chat.id, "Компьютер выключается...")
        os.system("shutdown /s /t 1")

    elif call.data == "cancel":
        bot.answer_callback_query(call.id, text="Отменено")
        bot.edit_message_text("Выключение отменено.", call.message.chat.id, call.message.message_id)


def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("📊 Текущий статус"),
        types.KeyboardButton("❓ Помощь"),
        types.KeyboardButton("⚙️ Меню")
    )
    return markup


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 Привет! Я бот для мониторинга сервера.\n\n"
        "📊 Нажми 'Текущий статус' чтобы увидеть CPU, RAM и Disk\n"
        "❓ Помощь — подсказки\n"
        "⚙️ Меню — другие функции",
        reply_markup=get_main_keyboard()
    )


@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    if message.chat.id != CHAT_ID:
        bot.reply_to(message, "⛔ Нет прав.")
        return

    if message.text == "📊 Текущий статус":
        cpu, ram, disk = get_metrics()
        status_text = (
            f"✅ Данные с сервера:\n"
            f"CPU: {cpu}%\n"
            f"RAM: {ram}%\n"
            f"Disk: {disk}%"
        )
        bot.send_message(message.chat.id, status_text, reply_markup=get_hardware_keyboard())

    elif message.text == "❓ Помощь":
        bot.send_message(message.chat.id, "Бот мониторит CPU, RAM и Disk твоего сервера. Нажимай кнопки внизу экрана!")

    elif message.text == "⚙️ Меню":
        bot.send_message(message.chat.id, "Меню:", reply_markup=get_menu_keyboard())


thread = threading.Thread(target=bot.infinity_polling, kwargs={"none_stop": True})
thread.start()
print("Бот успешно запущен в фоновом потоке.")

while True:
    time.sleep(1)