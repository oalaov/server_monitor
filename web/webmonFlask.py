from flask import Flask, render_template, jsonify
import psutil
import sqlite3
import json
from datetime import datetime
import os

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

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/metrics')
def get_metrics():
    return jsonify({
        'cpu': psutil.cpu_percent(interval=1),
        'ram': psutil.virtual_memory().percent,
        'disk': psutil.disk_usage('/').percent,
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

def run():
    if __name__ == '__main__':
        init_db()
        app.run(host='0.0.0.0', port=5000, debug=True)

run()