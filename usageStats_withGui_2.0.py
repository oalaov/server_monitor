import tkinter as tk
from tkinter import messagebox
import psutil
import datetime
import os  
import alerts

# Сообщение в телеграм
alerts.bot.send_message(alerts.CHAT_ID, "Система мониторинга запущена!", reply_markup=alerts.get_main_keyboard())

# Определяем путь к файлу лога в папке со скриптом
TIME_NAME = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, f"server_{TIME_NAME}.log")

def save_log(cpu_val, ram_val):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    if cpu_val > 80:
        log_string = f"WARNING HIGH CPU! [{now}] CPU: {cpu_val}% | RAM: {ram_val:.2f} GB\n"
    elif ram_val < 1:
        log_string = f"WARNING HIGH RAM USAGE! [{now}] CPU: {cpu_val}% | RAM: {ram_val:.2f} GB\n"
    else: 
        log_string = f"[{now}] CPU: {cpu_val}% | RAM: {ram_val:.2f} GB\n"
    with open(LOG_PATH, "a") as file:
        file.write(log_string)

def update_stats():
    # 1. Получаем данные
    cpu = psutil.cpu_percent()
    cpuCores = psutil.cpu_count()
    cpuFreq = psutil.cpu_freq().current
    ram = psutil.virtual_memory()
    ram_available_gb = ram.available / (1024**3)

    # 2. ВЫЗОВ ЛОГИРОВАНИЯ 
    save_log(cpu, ram_available_gb)

    # 3. Обновляем текст в окне
    cpu_label.config(text=f"CPU Load: {cpu}%", fg="white" if cpu < 80 else "red")
    cpuCores_label.config(text=f"CPU Cores: {cpuCores}", fg="white")
    cpuFreq_label.config(text=f"CPU Frequency: {cpuFreq}", fg="white")
    ram_label.config(text=f"RAM Available: {ram_available_gb:.4f} GB", 
                     fg="white" if ram_available_gb > 1 else "red")

    # 4. Логика Warning
    if cpu > 80:
        warning_label.config(text="!!! HIGH CPU LOAD !!!")
        alerts.send_notification(f"ВНИМАНИЕ! Нагрузка CPU: {cpu}%")
    elif ram_available_gb < 1:
        warning_label.config(text="!!! LOW MEMORY !!!")
        alerts.send_notification(f"ВНИМАНИЕ! Нагрузка CPU: {ram_available_gb}%")
    else:
        warning_label.config(text="")

    # 5. Запускаем обновление снова через 1 секунду
    root.after(1000, update_stats)

# --- СОЗДАНИЕ GUI ---
root = tk.Tk()
root.title("CPU and RAM Usage")
root.geometry("400x400")
root.configure(bg="#1e1e1e")

font_style = ("Arial", 14, "bold")

cpu_label = tk.Label(root, text="CPU: ...", font=font_style, bg="#1e1e1e", fg="white")
cpu_label.pack(pady=10)

cpuCores_label = tk.Label(root, text="CPU Cores: ...", font=font_style, bg="#1e1e1e", fg="white")
cpuCores_label.pack(pady=10)

cpuFreq_label = tk.Label(root, text="CPU Frequency: ...", font=font_style, bg="#1e1e1e", fg="white")
cpuFreq_label.pack(pady=10)

ram_label = tk.Label(root, text="RAM Available: ...", font=font_style, bg="#1e1e1e", fg="white")
ram_label.pack(pady=10)

warning_label = tk.Label(root, text="", font=("Arial", 12, "bold"), bg="#1e1e1e", fg="red")
warning_label.pack(pady=20)

# ПЕРВЫЙ ЗАПУСК
update_stats()

# ЗАПУСК ОКНА
root.mainloop()