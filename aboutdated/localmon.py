import tkinter as tk
from tkinter import messagebox
import psutil
import datetime
import os  
import alerts
import subprocess
import sys
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def launch_web_monitor():
    path_to_webmon = "webmon.py"
    command = [sys.executable, "-m", "streamlit", "run", path_to_webmon]
    
    try:
        subprocess.Popen(command, shell=True)
        print("Веб-интерфейс запускается...")
    except Exception as e:
        print(f"Ошибка при запуске: {e}")

# Сообщение в телеграм
alerts.bot.send_message(alerts.CHAT_ID, "🟢 Система мониторинга запущена!", reply_markup=alerts.get_main_keyboard())

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

    # Обновляем списки данных
    cpu_history.append(cpu)
    cpu_history.pop(0) # Удаляем старое значение, чтобы список не рос вечно

    # Обновляем данные на графике
    line_cpu.set_ydata(cpu_history)
    
    # Перерисовываем холст
    canvas.draw()

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

#                                           --- СОЗДАНИЕ GUI ---
cpu_history = [0] * 20
ram_history = [0] * 20
x_axis = list(range(20))

root = tk.Tk()
root.attributes("-topmost", True, "-alpha", 0.7)
root.overrideredirect(True)

root.title("CPU and RAM Usage")
root.geometry("300x400")
root.configure(bg="#1e1e1e")

font_style = ("Arial", 14, "bold")

# Панель управления
control_frame = tk.Frame(root, bg="#333333") # Темная полоска сверху
control_frame.pack(fill="x", side="top")

btn_web = tk.Button(root, text="Открыть Web-панель", command=launch_web_monitor)
btn_web.pack(pady=5)

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

#                                           --- УПРАВЛЕНИЕ ОКНОМ ---
# Функция закрытия
def quit_app():
    # English: Send a final message to Telegram and close
    alerts.bot.send_message(alerts.CHAT_ID, "🔴 Система мониторинга остановлена пользователем!")
    root.destroy()

# Функция сворачивания
def hide_window():
    root.withdraw() 

# Кнопка закрытия (Крестик)
close_button = tk.Button(control_frame, text=" Ⅹ ", bg="#cc0000", fg="white", 
                         bd=0, command=quit_app, font=("Arial", 10, "bold"))
close_button.pack(side="right")

# Кнопка сворачивания
hide_button = tk.Button(control_frame, text=" — ", bg="#555555", fg="white", 
                        bd=0, command=hide_window, font=("Arial", 10, "bold"))
hide_button.pack(side="right", padx=2)

# Функции для перетаскивания окна без рамки
def start_move(event):
    root.x = event.x
    root.y = event.y

def stop_move(event):
    root.x = None
    root.y = None

def do_move(event):
    deltax = event.x - root.x
    deltay = event.y - root.y
    x = root.winfo_x() + deltax
    y = root.winfo_y() + deltay
    root.geometry(f"+{x}+{y}")

# Привязываем события мыши к верхней панели
control_frame.bind("<ButtonPress-1>", start_move)
control_frame.bind("<ButtonRelease-1>", stop_move)
control_frame.bind("<B1-Motion>", do_move)

# Создаем фигуру matplotlib
fig = Figure(figsize=(4, 2), dpi=100, facecolor='#1e1e1e')
ax = fig.add_subplot(111)
ax.set_facecolor('#1e1e1e')

# Настройка осей, чтобы они были видны на темном фоне
ax.tick_params(colors='white')
for spine in ax.spines.values():
    spine.set_edgecolor('white')

# Рисуем начальные линии
line_cpu, = ax.plot(x_axis, cpu_history, color='#00ff00', label='CPU %')
ax.set_ylim(0, 100) # Проценты от 0 до 100

# Встраиваем график в Tkinter
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(pady=10, fill=tk.BOTH, expand=True)

# ПЕРВЫЙ ЗАПУСК
update_stats()

# ЗАПУСК ОКНА
root.mainloop()