import streamlit as st
import psutil
import time
import os
import ctypes
import pandas as pd

st.set_page_config(page_title="Server Monitor Pro", layout="wide")

# --- ЛОГИКА ДЛЯ НОВЫХ ФУНКЦИЙ ---

def get_last_logs():
    """Функция для чтения последних строк лога (если файла нет, создаем заглушку)"""
    if os.path.exists("server_log.txt"):
        with open("server_log.txt", "r", encoding="utf-8") as f:
            return f.readlines()[-10:] # Последние 10 строк
    return ["Лог-файл пока пуст..."]

def kill_heavy_process():
    """Находит и завершает самый прожорливый процесс по CPU"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        processes.append(proc.info)
    top_proc = max(processes, key=lambda x: x['cpu_percent'])
    # В реальной жизни тут был бы proc.terminate(), но для тестов просто вернем имя
    return top_proc['name']

# --- ИНТЕРФЕЙС: ВЕРХНЯЯ ПАНЕЛЬ ---
header_box = st.empty()
header_box.title("📊 Мониторинг сервера")

# Группа 1: Безопасность и Питание
st.subheader("🛡️ Управление и Безопасность")
c1, c2, c3, c4 = st.columns(4)

with c1:
    if st.button("🔒 Заблокировать", use_container_width=True, help="Win + L"):
        ctypes.windll.user32.LockWorkStation()
        st.toast("Рабочая станция заблокирована")

with c2:
    if st.button("💀 Убить процесс", use_container_width=True, help="Завершить самый тяжелый процесс"):
        name = kill_heavy_process()
        st.warning(f"Анализ завершен. Рекомендуется закрыть: {name}")

with c3:
    if st.button("🛑 Выключить", use_container_width=True):
        header_box.title("⚠️ Завершение работы...")
        # os.system("shutdown /s /t 5") # Закомментил, чтобы случайно не выключил при тесте
        st.toast("Команда на выключение отправлена")

with c4:
    st.link_button("✈️ Telegram Bot", url="https://t.me/serverAlertss_bot", use_container_width=True)

# Группа 2: Сеть и Отчеты (в Sidebar для порядка)
with st.sidebar:
    st.header("⚙️ Администрирование")
    
    if st.button("🌐 Проверить связь (Ping)"):
        # Имитация пинга (как Network Engineer ты оценишь)
        response = os.system("ping -n 1 8.8.8.8")
        if response == 0:
            st.success("Google (8.8.8.8) доступен")
        else:
            st.error("Проблемы с сетью!")

    st.divider()
    
    st.write("📂 **Работа с логами**")
    log_data = "\n".join(get_last_logs())
    st.download_button(
        label="📥 Скачать полный LOG",
        data=log_data,
        file_name="server_report.txt",
        mime="text/plain",
    )

    if st.button("🧹 Очистить историю графиков"):
        st.session_state.cpu_history = []
        st.session_state.ram_history = []
        st.rerun()

# --- ОСНОВНОЙ МОНИТОРИНГ ---
st.divider()
m_col1, m_col2 = st.columns(2)
cpu_metric_box = m_col1.empty()
ram_metric_box = m_col2.empty()

g_col1, g_col2 = st.columns(2)
cpu_chart_box = g_col1.empty()
ram_chart_box = g_col2.empty()

if 'cpu_history' not in st.session_state:
    st.session_state.cpu_history = []
if 'ram_history' not in st.session_state:
    st.session_state.ram_history = []

while True:
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    ram_avail = psutil.virtual_memory().available / (1024**3)

    st.session_state.cpu_history.append(cpu)
    st.session_state.ram_history.append(ram)
    
    if len(st.session_state.cpu_history) > 30:
        st.session_state.cpu_history.pop(0)
    if len(st.session_state.ram_history) > 30:
        st.session_state.ram_history.pop(0)

    # Динамический заголовок
    if cpu > 80:
        header_box.error(f"❗ КРИТИЧЕСКАЯ НАГРУЗКА: {cpu}% ❗")
    else:
        header_box.title("📊 Мониторинг сервера")

    cpu_metric_box.metric("Процессор (CPU)", f"{cpu}%")
    ram_metric_box.metric("Память (RAM)", f"{ram}%", delta=f"{ram_avail:.2f} GB свободно")

    cpu_chart_box.area_chart(st.session_state.cpu_history) # Area chart выглядит круче
    ram_chart_box.area_chart(st.session_state.ram_history)

    time.sleep(0.5)