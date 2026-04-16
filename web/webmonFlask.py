from flask import Flask, render_template, jsonify
import psutil
import sqlite3
from datetime import datetime
import os
import requests
import threading
import time

cpu_prev = {}
cpu_prev_time = None
CPU_CORES = None

app = Flask(__name__)

DB_PATH = os.environ.get('DB_PATH', 'server_monitor.db')

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
    

def get_ram_from_windows_exporter():
    try:
        resp = requests.get('http://host.docker.internal:9182/metrics', timeout=2)
        lines = resp.text.split('\n')
        
        total = None
        available = None
        
        for line in lines:
            if 'windows_memory_physical_total_bytes' in line:
                try:
                    total = float(line.split()[1])
                except:
                    pass
            if 'windows_memory_available_bytes' in line:
                try:
                    available = float(line.split()[1])
                except:
                    pass
        
        if total and available and total > 0:
            used_percent = (1 - available / total) * 100
            return round(used_percent, 1)
        
        print(f"⚠️ RAM не найдена: total={total}, available={available}")
        return None
    except Exception as e:
        print(f"Windows Exporter RAM не ответил: {e}")
        return None

def get_disk_from_windows_exporter():
    try:
        resp = requests.get('http://host.docker.internal:9182/metrics', timeout=2)
        lines = resp.text.split('\n')
        
        size = None
        free = None
        
        for line in lines:
            if 'windows_logical_disk_size_bytes{volume="C:"}' in line:
                try:
                    size = float(line.split()[1])
                except:
                    pass
            if 'windows_logical_disk_free_bytes{volume="C:"}' in line:
                try:
                    free = float(line.split()[1])
                except:
                    pass
        
        if size and free is not None and size > 0:
            used_percent = (1 - free / size) * 100
            return round(used_percent, 1)
        
        print(f"⚠️ Диск C: не найден: size={size}, free={free}")
        return None
    except Exception as e:
        print(f"Windows Exporter диск не ответил: {e}")
        return None

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/metrics')
def get_metrics():
    cpu_percent = get_cpu_from_windows_exporter()
    ram_percent = get_ram_from_windows_exporter()
    disk_percent = get_disk_from_windows_exporter()
    
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
            ram = get_ram_from_windows_exporter()
            disk = get_disk_from_windows_exporter()
            
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