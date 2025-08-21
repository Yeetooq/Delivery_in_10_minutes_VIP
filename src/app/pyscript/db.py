import sqlite3
import os

# Путь к базе данных внутри проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
DB_PATH = os.path.join(DATA_DIR, "users.db")

# Убедимся, что папка data существует
os.makedirs(DATA_DIR, exist_ok=True)

def init_db():
    print(f"[DB] 📂 Используется база данных: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print("[DB] ✅ Таблица users инициализирована")

def register_user(username, email, password):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, password)
        )
        conn.commit()

        # Проверим, что юзер добавлен
        cursor.execute("SELECT id, username, email FROM users")
        all_users = cursor.fetchall()
        print(f"[DB] 👤 Зарегистрирован: {username}")
        print(f"[DB] 📋 Все пользователи: {all_users}")

        conn.close()
        return True
    except sqlite3.IntegrityError:
        print(f"[DB] ⚠️ Пользователь с email {email} уже существует")
        return False

def login_user(email, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE email = ? AND password = ?",
        (email, password)
    )
    user = cursor.fetchone()
    conn.close()
    if user:
        print(f"[DB] ✅ Успешный вход: {email}")
        return True
    else:
        print(f"[DB] ❌ Неверный логин или пароль для {email}")
        return False
