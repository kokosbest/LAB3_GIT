# Подключение к базе данных и инициализация
import sqlite3
import datetime
import hashlib
from config import Config


class DatabaseConnection:
    def __init__(self, db_path: str = Config.DB_NAME):
        self.db_path = db_path

    def get_connection(self):
        """Возвращает соединение с базой данных"""
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Инициализация базы данных"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                full_name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')

        # Таблица заявок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                priority TEXT NOT NULL DEFAULT 'medium',
                created_by INTEGER NOT NULL,
                assigned_to INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (assigned_to) REFERENCES users(id)
            )
        ''')

        conn.commit()
        conn.close()

        self._create_default_users()

    def _hash_password(self, password: str) -> str:
        """Хеширование пароля"""
        return hashlib.sha256(password.encode()).hexdigest()

    def _create_default_users(self):
        """Создание пользователей по умолчанию"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Проверяем, есть ли уже пользователи
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            # Создаем пользователя
            user_password = self._hash_password("user123")
            cursor.execute('''
                INSERT INTO users (username, password_hash, role, full_name, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', ("user", user_password, "user", "Обычный пользователь", datetime.datetime.now().isoformat()))

            # Создаем саппорта
            support_password = self._hash_password("support123")
            cursor.execute('''
                INSERT INTO users (username, password_hash, role, full_name, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', ("support", support_password, "support", "Специалист поддержки", datetime.datetime.now().isoformat()))

            print("Созданы пользователи по умолчанию:")
            print("  Пользователь: логин 'user', пароль 'user123'")
            print("  Саппорт: логин 'support', пароль 'support123'")

        conn.commit()
        conn.close()