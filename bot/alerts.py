import telebot
import time
import psutil
import threading
import os
import subprocess
import keyboard
import ctypes
from telebot import types

#TOKEN AND CHAT ID
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID", "7926748416")

bot = telebot.TeleBot(TOKEN)
last_alert_time = 0 

def get_hardware_health():
    battery = psutil.sensors_battery()
    if battery:
        percent = battery.percent
        power_plugged = "Подключена 🔌" if battery.power_plugged else "Работает от батареи 🔋"
        battery_status = f"Заряд: {percent}% ({power_plugged})"
    else:
        battery_status = "Батарея не обнаружена"
    return f"🔋 {battery_status}"

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

def lock_screen():
    ctypes.windll.user32.LockWorkStation()

def get_ping_result(host="8.8.8.8"):
    try:
        output = subprocess.check_output(f"ping -n 2 {host}", shell=True, stderr=subprocess.STDOUT)
        return output.decode('cp866')
    
    except Exception as e:
        return f"Ошибка связи: {e}"

def get_menu_keyboard():
    markup = types.InlineKeyboardMarkup()

    menu_firstButton = types.InlineKeyboardButton("Пока не работает :)", callback_data="menu_firstButton")

    markup.add(menu_firstButton)
    return markup

def get_hardware_keyboard():
    markup = types.InlineKeyboardMarkup()

    btn_hardware = types. InlineKeyboardButton("Полные данные по железу", callback_data="get_hardware")

    markup.add(btn_hardware)
    return markup

def get_inline_keyboard():
    markup = types.InlineKeyboardMarkup()
    
    btn_yes = types.InlineKeyboardButton("Да, выключай", callback_data="confirm_shutdown")
    btn_no = types.InlineKeyboardButton("Нет, отмена", callback_data="cancel")
    
    markup.add(btn_yes, btn_no)
    return markup

@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    cpu = psutil.cpu_percent(interval=0.5) 
    ram = psutil.virtual_memory().available / (1024**3)
    hardware = get_hardware_health()

    if call.data == "get_hardware":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"\nCPU: {cpu}%\nRAM доступно: {ram:.2f} GB \n {hardware}")
    
    elif call.data == "menu_firstButton":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text= "Пока не работает :)")

    elif call.data == "confirm_shutdown":
        bot.answer_callback_query(call.id, text="Выполняю!") # Всплывающее уведомление
        bot.send_message(call.message.chat.id, "Компьютер выключается...")
        os.system("shutdown /s /t 1")
        
    elif call.data == "cancel":
        bot.answer_callback_query(call.id, text="Отменено")
        bot.edit_message_text("Выключение отменено.", call.message.chat.id, call.message.message_id)

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_status = types.KeyboardButton("📊 Текущий статус")
    btn_menu = types.KeyboardButton("⚙️ Меню")
    btn_help = types.KeyboardButton("❓ Помощь")
    btn_ping = types.KeyboardButton("🛜 Пинг (До google.com)")
    btn_lock = types.KeyboardButton("🔒 Заблокировать сервер")
    btn_kill = types.KeyboardButton("❌ Выключить сервер")
    markup.add(btn_status, btn_help, btn_kill, btn_ping, btn_menu, btn_lock)
    return markup

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    if message.text == "📊 Текущий статус":

        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory().available / (1024**3)

        
        status_text = f"✅ Данные с сервера:\nCPU: {cpu}%\nRAM доступно: {ram:.2f} GB"
        bot.send_message(message.chat.id, status_text, reply_markup=get_hardware_keyboard())
    
    elif message.text == "❓ Помощь":
        bot.send_message(message.chat.id, "Бот мониторит CPU и RAM твоего сервера. Нажимай кнопки внизу экрана!")
    
    elif message.text == "❌ Выключить сервер":
        bot.send_message(message.chat.id, "Вы точно хотите выключить сервер?", reply_markup=get_inline_keyboard())

    elif message.text == "🛜Пинг (До google.com)":
        bot.send_message(message.chat.id, get_ping_result())

    elif message.text == "⚙️ Меню":
        bot.send_message(message.chat.id, "Меню:", reply_markup=get_menu_keyboard())

    elif message.text == "🔒 Заблокировать сервер":
        lock_screen()
        bot.send_message(message.chat.id, "Сервер заблокирован (Win + L)")
    


thread = threading.Thread(target=bot.infinity_polling, kwargs={"none_stop": True})
thread.start()
print("Бот успешно запущен в фоновом потоке.")

while True:
    time.sleep(1)
