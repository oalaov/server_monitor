import tkinter as tk
from tkinter import messagebox
import psutil
import datetime

def update_stats():
    # Получаем данные
    cpu = psutil.cpu_percent()
    cpuCores = psutil.cpu_count()
    cpuFreq = psutil.cpu_freq().current
    ram = psutil.virtual_memory()
    ram_available_gb = ram.available / (1024**3)
    save_log(cpu, ram_available_gb)


    # Обновляем текст в окне
    cpu_label.config(text=f"CPU Load: {cpu}%", fg="white" if cpu < 80 else "red")
    cpuCores_label.config(text=f"CPU Cores: {cpuCores}", fg="white")
    cpuFreq_label.config(text=f"CPU Frequency: {cpuFreq}", fg="white")
    ram_label.config(text=f"RAM Available: {ram_available_gb:.4f} GB", 
                     fg="white" if ram_available_gb > 1 else "red")

    # Твоя логика Warning (теперь через всплывающее окно!)
    if cpu > 80:
        warning_label.config(text="!!! HIGH CPU LOAD !!!")
    elif ram_available_gb < 1:
        warning_label.config(text="!!! LOW MEMORY !!!")
    else:
        warning_label.config(text="")

    # Запускаем обновление снова через 1000мс (1 секунда)
    root.after(1000, update_stats)

    #ЛОГИ

def save_log(cpu_val, ram_val):
    
    
    # 1. Формируем время (Timestamp)
    now = datetime.datetime.now().strftime("%H:%M:%S")
    
    # 2. Формируем строку лога
    log_string = f"[{now}] CPU: {cpu_val}% | RAM: {ram_val:.2f} GB\n"
    
    # 3. Открываем файл и записываем (File I/O)
    with open("server.log", "a") as file:
        file.write(log_string)

# Запускаем обновление снова через 1000мс (1 секунда)
    root.after(1000, update_stats)


# Создаем главное окно
root = tk.Tk()
root.title("CPU and RAM Usage")
root.geometry("400x400")
root.configure(bg="#1e1e1e") # Темная тема, как мы любим

# Дизайн надписей
font_style = ("Arial", 14, "bold")

cpu_label = tk.Label(root, text="CPU: ...", font=font_style, bg="#1e1e1e", fg="white")
cpu_label.pack(pady=10)

cpuCores_label = tk.Label(root, text="CPU: ...", font=font_style, bg="#1e1e1e", fg="white")
cpuCores_label.pack(pady=10)

cpuFreq_label = tk.Label(root, text="CPU: ...", font=font_style, bg="#1e1e1e", fg="white")
cpuFreq_label.pack(pady=10)

ram_label = tk.Label(root, text="RAM: ...", font=font_style, bg="#1e1e1e", fg="white")
ram_label.pack(pady=10)

warning_label = tk.Label(root, text="", font=("Arial", 12, "bold"), bg="#1e1e1e", fg="red")
warning_label.pack(pady=20)

# Запуск цикла обновления
update_stats()

# Запуск окна
root.mainloop()

