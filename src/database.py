import sqlite3
from datetime import datetime

DB_PATH = "data/history.db"

def init_db():
    # Создает таблицу для хранения истории анализов, если её нет.
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            filename TEXT,
            transcription TEXT,
            verdict TEXT,
            confidence INTEGER,
            recommendation TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_result(filename, transcription, analysis):
    # Сохраняет данные анализа в базу.
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO audit_log (timestamp, filename, transcription, verdict, confidence, recommendation)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        filename,
        transcription,
        analysis.get("verdict", "UNKNOWN"),
        analysis.get("confidence_score", 0),
        analysis.get("recommendation", "")
    ))
    conn.commit()
    conn.close()

def get_history():
    # Возвращает все записи из истории.
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM audit_log ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows