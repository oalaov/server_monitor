from flask import Flask, render_template, jsonify, session, redirect, url_for, request
from functools import wraps
from dotenv import load_dotenv
import psutil
import sqlite3
from datetime import datetime
import os
import requests
import threading
import time



app = Flask(__name__)

cpu_lock = threading.Lock()

app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise ValueError("В файле .env отсуствует SECRET_KEY")

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
if not ADMIN_USERNAME:
    raise ValueError("В файле .env отсуствует ADMIN_USERNAME")

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
if not ADMIN_PASSWORD:
    raise ValueError("В файле .env отсуствует ADMIN_PASSWORD")

cpu_prev = {}
cpu_prev_time = None
CPU_CORES = None

DB_PATH = os.environ.get('DB_PATH', 'server_monitor.db')

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            error = 'Неверный логин или пароль'
    
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            message TEXT NOT NULL,
            severity TEXT DEFAULT 'INFO'
        )
    ''')
    conn.commit()
    conn.close()

    

def get_cpu_from_windows_exporter():
    global cpu_prev, cpu_prev_time, CPU_CORES
    with cpu_lock:
        try:
            resp = requests.get('http://host.docker.internal:9182/metrics', timeout=2)
            lines = resp.text.split('\n')
        
            core_total = {}
            core_idle = {}
        
            for line in lines:
                if 'windows_cpu_time_total' in line and 'core="' in line:
                    try:
                        core_part = line.split('core="')[1].split('"')[0]
                        mode_part = line.split('mode="')[1].split('"')[0] if 'mode="' in line else ''
                        parts = line.split()
                        if len(parts) >= 2:
                            value = float(parts[1])
                        
                            if core_part not in core_total:
                                core_total[core_part] = 0.0
                                core_idle[core_part] = 0.0
                        
                            core_total[core_part] += value
                        
                            if mode_part == 'idle':
                                core_idle[core_part] += value
                    except:
                        continue
        
            if not core_total:
                return None
        
            total_all = sum(core_total.values())
            idle_all = sum(core_idle.values())
        
            if CPU_CORES is None:
                CPU_CORES = len(core_total)
        
            now = datetime.now().timestamp()
        
            if cpu_prev_time is None or 'total' not in cpu_prev:
                cpu_prev['total'] = total_all
                cpu_prev['idle'] = idle_all
                cpu_prev_time = now
                return 0.0
        
            time_delta = now - cpu_prev_time
            if time_delta <= 0:
                return 0.0
        
            total_delta = total_all - cpu_prev['total']
            idle_delta = idle_all - cpu_prev['idle']
        
            active_delta = total_delta - idle_delta
        
            if total_delta <= 0:
                return 0.0
        
            cpu_percent = (active_delta / total_delta) * 100
            cpu_percent = min(100, max(0, cpu_percent))
        
            cpu_prev['total'] = total_all
            cpu_prev['idle'] = idle_all
            cpu_prev_time = now
        
            return round(cpu_percent, 1)
        
        except Exception as e:
            print(f"Windows Exporter CPU не ответил: {e}")
        return None
    
    
def get_ram_and_disk_from_windows_exporter():
    try:
        resp = requests.get('http://host.docker.internal:9182/metrics', timeout=2)
        lines = resp.text.split('\n')
        
        total_ram = None
        available_ram = None
        disk_size = None
        disk_free = None
        
        for line in lines:
            if line.startswith('#'):
                continue
            
            if 'windows_memory_physical_total_bytes' in line:
                parts = line.split()
                if len(parts) >= 2:
                    total_ram = float(parts[1])
            elif 'windows_memory_available_bytes' in line:
                parts = line.split()
                if len(parts) >= 2:
                    available_ram = float(parts[1])
            elif 'windows_logical_disk_size_bytes{volume="C:"}' in line:
                parts = line.split()
                if len(parts) >= 2:
                    disk_size = float(parts[1])
            elif 'windows_logical_disk_free_bytes{volume="C:"}' in line:
                parts = line.split()
                if len(parts) >= 2:
                    disk_free = float(parts[1])
        
        ram_percent = None
        if total_ram and available_ram and total_ram > 0:
            ram_percent = round((1 - available_ram / total_ram) * 100, 1)
        
        disk_percent = None
        if disk_size and disk_free is not None and disk_size > 0:
            disk_percent = round((1 - disk_free / disk_size) * 100, 1)
        
        return ram_percent, disk_percent
        
    except Exception as e:
        print(f"❌ Ошибка в get_ram_and_disk_from_windows_exporter: {e}")
        import traceback
        traceback.print_exc()
        return None, None

@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/metrics')
@login_required
def get_metrics():
    cpu_percent = get_cpu_from_windows_exporter()
    ram_percent, disk_percent = get_ram_and_disk_from_windows_exporter()
    
    if cpu_percent is None:
        cpu_percent = psutil.cpu_percent(interval=1)
    if ram_percent is None:
        ram_percent = psutil.virtual_memory().percent
    if disk_percent is None:
        disk_percent = psutil.disk_usage('/').percent
    
    return jsonify({
        'cpu': cpu_percent,
        'ram': ram_percent,
        'disk': disk_percent,
        'time': datetime.now().strftime('%H:%M:%S')
    })

@app.route('/api/alerts')
def get_alerts():
    conn = get_db_connection()
    alerts = conn.execute('''
        SELECT timestamp, message, severity 
        FROM alerts 
        ORDER BY timestamp DESC 
        LIMIT 50
    ''').fetchall()
    conn.close()
    return jsonify([dict(alert) for alert in alerts])

@app.route('/api/test_alert', methods=['POST'])
def test_alert():
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO alerts (timestamp, message, severity)
        VALUES (?, ?, ?)
    ''', (datetime.now().isoformat(), 'Test alert from web', 'INFO'))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


def check_metrics_and_alert():
    CPU_THRESHOLD = 30   # 30%
    RAM_THRESHOLD = 50   # 50%
    DISK_THRESHOLD = 70  # 70%
    
    last_alert = {'cpu': 0, 'ram': 0, 'disk': 0}
    
    print("🟢 Фоновый мониторинг запущен с реальными метриками")
    
    while True:
        try:
            cpu = get_cpu_from_windows_exporter()
            ram, disk = get_ram_and_disk_from_windows_exporter()
            
            if cpu is None:
                cpu = psutil.cpu_percent(interval=1)
                print(f"⚠️ CPU взят из psutil: {cpu}%")
            if ram is None:
                ram = psutil.virtual_memory().percent
                print(f"⚠️ RAM взята из psutil: {ram}%")
            if disk is None:
                disk = psutil.disk_usage('/').percent
                print(f"⚠️ Disk взят из psutil: {disk}%")
            
            print(f"📊 Метрики: CPU={cpu}% | RAM={ram}% | DISK={disk}%")
            
            now = datetime.now().isoformat()
            conn = get_db_connection()
            
            if cpu > CPU_THRESHOLD:
                last = last_alert.get('cpu', 0)
                if time.time() - last > 600:  
                    message = f"⚠️ ВЫСОКАЯ ЗАГРУЗКА CPU: {cpu}% (порог {CPU_THRESHOLD}%)"
                    conn.execute('''
                        INSERT INTO alerts (timestamp, message, severity)
                        VALUES (?, ?, ?)
                    ''', (now, message, 'WARNING'))
                    conn.commit()
                    last_alert['cpu'] = time.time()
                    print(f"🔔 Алерт: {message}")
            
            if ram > RAM_THRESHOLD:
                last = last_alert.get('ram', 0)
                if time.time() - last > 600:
                    message = f"⚠️ ВЫСОКОЕ ИСПОЛЬЗОВАНИЕ RAM: {ram}% (порог {RAM_THRESHOLD}%)"
                    conn.execute('''
                        INSERT INTO alerts (timestamp, message, severity)
                        VALUES (?, ?, ?)
                    ''', (now, message, 'WARNING'))
                    conn.commit()
                    last_alert['ram'] = time.time()
                    print(f"🔔 Алерт: {message}")
            
            if disk > DISK_THRESHOLD:
                last = last_alert.get('disk', 0)
                if time.time() - last > 600:
                    message = f"⚠️ ЗАПОЛНЕНИЕ ДИСКА C:: {disk}% (порог {DISK_THRESHOLD}%)"
                    conn.execute('''
                        INSERT INTO alerts (timestamp, message, severity)
                        VALUES (?, ?, ?)
                    ''', (now, message, 'WARNING'))
                    conn.commit()
                    last_alert['disk'] = time.time()
                    print(f"🔔 Алерт: {message}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Ошибка в фоновом мониторинге: {e}")
            import traceback
            traceback.print_exc()
        
        time.sleep(30)

monitor_thread = threading.Thread(target=check_metrics_and_alert, daemon=True)
monitor_thread.start()
print("✅ Фоновый мониторинг запущен (проверка каждые 30 секунд)")


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)