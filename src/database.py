import sqlite3
from datetime import datetime

DB_PATH = "data/history.db"

def init_db():
    """
    Инициализирует базу данных SQLite.
    Создает таблицу audit_log, если она еще не существует.
    Колонки: id, время, имя файла, текст, вердикт, уверенность, анализ и рекомендации.
    """
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
            analysis TEXT,
            recommendation TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_result(filename, transcription, analysis): # Сохраняет результаты анализа одного звонка в базу данных.
    """
    Аргументы:
    - filename: имя обработанного аудиофайла.
    - transcription: текст, полученный после распознавания речи.
    - analysis: словарь (JSON) с результатами от Gemini (вердикт, скоринг и т.д.).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO audit_log (timestamp, filename, transcription, verdict, confidence, analysis, recommendation)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        filename,
        transcription,
        analysis.get("verdict", "UNKNOWN"),
        analysis.get("confidence_score", 0),
        analysis.get("analysis", ""),
        analysis.get("recommendation", "")
    ))
    conn.commit()
    conn.close()

def get_history():  
    """
    Извлекает всю историю проверок из базы данных.
    Сортирует записи по времени: самые свежие будут в начале списка (DESC).
    
    Возвращает:
    - rows: список кортежей с данными всех проверок.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM audit_log ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_record(record_id):  # Удаляет конкретную запись из базы по ID.
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM audit_log WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()