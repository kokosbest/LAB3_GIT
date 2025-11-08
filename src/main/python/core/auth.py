# Аутентификация и авторизация
import sqlite3
import datetime
from typing import Optional, Tuple
from database.connection import DatabaseConnection
from database.models import User


class AuthManager:
    def __init__(self, db_connection: DatabaseConnection):
        self.db_connection = db_connection
        self.current_user = None

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Аутентификация пользователя"""
        conn = self.db_connection.get_connection()
        cursor = conn.cursor()

        password_hash = self.db_connection._hash_password(password)

        cursor.execute('''
            SELECT id, username, role, full_name, created_at
            FROM users 
            WHERE username = ? AND password_hash = ?
        ''', (username, password_hash))

        user_data = cursor.fetchone()
        conn.close()

        if user_data:
            return User(*user_data)
        return None

    def register_user(self, username: str, password: str, full_name: str, role: str = "user") -> bool:
        """Регистрация нового пользователя"""
        conn = self.db_connection.get_connection()
        cursor = conn.cursor()

        try:
            # Проверяем, существует ли пользователь
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                conn.close()
                return False

            password_hash = self.db_connection._hash_password(password)
            current_time = datetime.datetime.now().isoformat()

            cursor.execute('''
                INSERT INTO users (username, password_hash, role, full_name, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, role, full_name, current_time))

            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
        except Exception as e:
            print(f"Ошибка при регистрации: {e}")
            conn.close()
            return False

    def login(self, username: str, password: str) -> bool:
        """Вход в систему"""
        user = self.authenticate_user(username, password)
        if user:
            self.current_user = user
            return True
        return False

    def logout(self):
        """Выход из системы"""
        self.current_user = None

    def is_authenticated(self) -> bool:
        """Проверка аутентификации"""
        return self.current_user is not None

    def is_support(self) -> bool:
        """Проверка роли поддержки"""
        return self.is_authenticated() and self.current_user.role == 'support'