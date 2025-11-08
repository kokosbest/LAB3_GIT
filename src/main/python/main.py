import sqlite3
import datetime
import textwrap
import hashlib
import json
import csv
import xml.etree.ElementTree as ET
import yaml
import os
from typing import List, Tuple, Optional, Dict, Any


class SupportTicketSystem:
    def __init__(self, db_name: str = "support_tickets.db"):
        self.db_name = db_name
        self.current_user = None
        self.init_database()

    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        conn = sqlite3.connect(self.db_name)
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

        # Создаем начальных пользователей, если их нет
        self._create_default_users()

    def _create_default_users(self):
        """Создание пользователей по умолчанию"""
        conn = sqlite3.connect(self.db_name)
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

    def _hash_password(self, password: str) -> str:
        """Хеширование пароля"""
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate_user(self, username: str, password: str) -> Optional[Tuple]:
        """Аутентификация пользователя"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        password_hash = self._hash_password(password)

        cursor.execute('''
            SELECT id, username, role, full_name 
            FROM users 
            WHERE username = ? AND password_hash = ?
        ''', (username, password_hash))

        user = cursor.fetchone()
        conn.close()

        return user

    def register_user(self, username: str, password: str, full_name: str, role: str = "user") -> bool:
        """Регистрация нового пользователя"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        try:
            # Проверяем, существует ли пользователь
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                conn.close()
                return False

            password_hash = self._hash_password(password)

            cursor.execute('''
                INSERT INTO users (username, password_hash, role, full_name, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, role, full_name, datetime.datetime.now().isoformat()))

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

    def add_ticket(self, title: str, description: str, priority: str = "medium") -> int:
        """Добавление новой заявки"""
        if not self.current_user:
            raise Exception("Пользователь не аутентифицирован")

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        current_time = datetime.datetime.now().isoformat()

        cursor.execute('''
            INSERT INTO tickets (title, description, priority, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, description, priority, self.current_user[0], current_time, current_time))

        ticket_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return ticket_id

    def get_all_tickets(self) -> List[Tuple]:
        """Получение всех заявок"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        if self.current_user[2] == 'support':
            # Саппорт видит все заявки
            cursor.execute('''
                SELECT t.id, t.title, t.description, t.status, t.priority, 
                       u1.full_name as created_by, u2.full_name as assigned_to,
                       t.created_at, t.updated_at
                FROM tickets t
                LEFT JOIN users u1 ON t.created_by = u1.id
                LEFT JOIN users u2 ON t.assigned_to = u2.id
                ORDER BY 
                    CASE priority 
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'low' THEN 3
                    END,
                    t.created_at DESC
            ''')
        else:
            # Пользователь видит только свои заявки
            cursor.execute('''
                SELECT t.id, t.title, t.description, t.status, t.priority, 
                       u1.full_name as created_by, u2.full_name as assigned_to,
                       t.created_at, t.updated_at
                FROM tickets t
                LEFT JOIN users u1 ON t.created_by = u1.id
                LEFT JOIN users u2 ON t.assigned_to = u2.id
                WHERE t.created_by = ?
                ORDER BY 
                    CASE priority 
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'low' THEN 3
                    END,
                    t.created_at DESC
            ''', (self.current_user[0],))

        tickets = cursor.fetchall()
        conn.close()

        return tickets

    def get_ticket(self, ticket_id: int) -> Optional[Tuple]:
        """Получение конкретной заявки по ID"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        if self.current_user[2] == 'support':
            cursor.execute('''
                SELECT t.id, t.title, t.description, t.status, t.priority, 
                       u1.full_name as created_by, u2.full_name as assigned_to,
                       t.created_at, t.updated_at
                FROM tickets t
                LEFT JOIN users u1 ON t.created_by = u1.id
                LEFT JOIN users u2 ON t.assigned_to = u2.id
                WHERE t.id = ?
            ''', (ticket_id,))
        else:
            cursor.execute('''
                SELECT t.id, t.title, t.description, t.status, t.priority, 
                       u1.full_name as created_by, u2.full_name as assigned_to,
                       t.created_at, t.updated_at
                FROM tickets t
                LEFT JOIN users u1 ON t.created_by = u1.id
                LEFT JOIN users u2 ON t.assigned_to = u2.id
                WHERE t.id = ? AND t.created_by = ?
            ''', (ticket_id, self.current_user[0]))

        ticket = cursor.fetchone()
        conn.close()

        return ticket

    def update_ticket_status(self, ticket_id: int, status: str):
        """Обновление статуса заявки"""
        if not self.current_user:
            raise Exception("Пользователь не аутентифицирован")

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        current_time = datetime.datetime.now().isoformat()

        cursor.execute('''
            UPDATE tickets 
            SET status = ?, updated_at = ?
            WHERE id = ?
        ''', (status, current_time, ticket_id))

        conn.commit()
        conn.close()

    def assign_ticket(self, ticket_id: int, user_id: int):
        """Назначение заявки на саппорта"""
        if self.current_user[2] != 'support':
            raise Exception("Только саппорт может назначать заявки")

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        current_time = datetime.datetime.now().isoformat()

        cursor.execute('''
            UPDATE tickets 
            SET assigned_to = ?, updated_at = ?, status = 'in_progress'
            WHERE id = ?
        ''', (user_id, current_time, ticket_id))

        conn.commit()
        conn.close()

    def delete_ticket(self, ticket_id: int):
        """Удаление заявки"""
        if not self.current_user:
            raise Exception("Пользователь не аутентифицирован")

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        if self.current_user[2] == 'support':
            cursor.execute('DELETE FROM tickets WHERE id = ?', (ticket_id,))
        else:
            cursor.execute('DELETE FROM tickets WHERE id = ? AND created_by = ?', (ticket_id, self.current_user[0]))

        conn.commit()
        conn.close()


class DataExporter:
    """Класс для экспорта данных в различные форматы"""

    def __init__(self, db_path: str = "support_tickets.db"):
        self.db_path = db_path
        self.output_dir = "out"
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        """Создает папку out, если её нет"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def get_table_structure(self, table_name: str) -> List[Dict[str, str]]:
        """Получает структуру таблицы"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        structure = []
        for col in columns:
            structure.append({
                'name': col[1],
                'type': col[2],
                'notnull': col[3],
                'default': col[4],
                'pk': col[5]
            })

        conn.close()
        return structure

    def get_foreign_keys(self, table_name: str) -> List[Dict[str, str]]:
        """Получает информацию о внешних ключах"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        foreign_keys = cursor.fetchall()

        fk_info = []
        for fk in foreign_keys:
            fk_info.append({
                'table': fk[2],
                'from': fk[3],
                'to': fk[4]
            })

        conn.close()
        return fk_info

    def get_related_data(self, table_name: str, foreign_key: str, related_table: str, key_value: Any) -> Dict[str, Any]:
        """Получает связанные данные по внешнему ключу"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM {related_table} WHERE id = ?", (key_value,))
        related_row = cursor.fetchone()

        if not related_row:
            conn.close()
            return {}

        # Получаем названия колонок
        cursor.execute(f"PRAGMA table_info({related_table})")
        columns = [col[1] for col in cursor.fetchall()]

        related_data = dict(zip(columns, related_row))
        conn.close()

        return related_data

    def export_table_data(self, table_name: str):
        """Экспортирует данные таблицы во все форматы"""
        print(f"\nЭкспорт данных из таблицы: {table_name}")

        # Получаем данные
        data = self._get_table_data_with_relations(table_name)

        # Экспорт в различные форматы
        self._export_to_json(data)
        self._export_to_csv(data)
        self._export_to_xml(data)
        self._export_to_yaml(data)

        print("✓ Экспорт завершен! Файлы созданы в папке 'out'")

    def _get_table_data_with_relations(self, table_name: str) -> List[Dict[str, Any]]:
        """Получает данные таблицы с связанными данными"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Получаем структуру таблицы
        structure = self.get_table_structure(table_name)
        column_names = [col['name'] for col in structure]

        # Получаем внешние ключи
        foreign_keys = self.get_foreign_keys(table_name)

        # Получаем данные
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        # Преобразуем в список словарей
        data = []
        for row in rows:
            row_dict = dict(zip(column_names, row))

            # Добавляем связанные данные для каждого внешнего ключа
            for fk in foreign_keys:
                fk_column = fk['from']
                related_table = fk['table']

                if fk_column in row_dict and row_dict[fk_column] is not None:
                    related_data = self.get_related_data(
                        table_name, fk_column, related_table, row_dict[fk_column]
                    )
                    if related_data:
                        # Создаем вложенную структуру для связанных данных
                        relation_name = f"{related_table}"
                        row_dict[relation_name] = related_data

            data.append(row_dict)

        conn.close()
        return data

    def _export_to_json(self, data: List[Dict[str, Any]]):
        """Экспорт в JSON"""
        output_path = os.path.join(self.output_dir, "data.json")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✓ JSON: {output_path}")

    def _export_to_csv(self, data: List[Dict[str, Any]]):
        """Экспорт в CSV"""
        output_path = os.path.join(self.output_dir, "data.csv")

        if not data:
            return

        # Получаем все возможные ключи (включая вложенные)
        all_keys = set()
        for row in data:
            for key, value in row.items():
                if isinstance(value, dict):
                    # Для вложенных словарей добавляем префикс
                    for sub_key in value.keys():
                        all_keys.add(f"{key}_{sub_key}")
                else:
                    all_keys.add(key)

        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
            writer.writeheader()

            for row in data:
                # Преобразуем вложенные словари в плоскую структуру для CSV
                flat_row = {}
                for key, value in row.items():
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            flat_row[f"{key}_{sub_key}"] = sub_value
                    else:
                        flat_row[key] = value

                writer.writerow(flat_row)

        print(f"✓ CSV: {output_path}")

    def _export_to_xml(self, data: List[Dict[str, Any]]):
        """Экспорт в XML"""
        output_path = os.path.join(self.output_dir, "data.xml")

        root = ET.Element('data')

        for row in data:
            record_element = ET.SubElement(root, 'record')

            for key, value in row.items():
                if isinstance(value, dict):
                    # Обрабатываем вложенные данные
                    relation_element = ET.SubElement(record_element, key)
                    for sub_key, sub_value in value.items():
                        sub_element = ET.SubElement(relation_element, sub_key)
                        sub_element.text = str(sub_value) if sub_value is not None else ''
                else:
                    element = ET.SubElement(record_element, key)
                    element.text = str(value) if value is not None else ''

        tree = ET.ElementTree(root)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)

        print(f"✓ XML: {output_path}")

    def _export_to_yaml(self, data: List[Dict[str, Any]]):
        """Экспорт в YAML"""
        output_path = os.path.join(self.output_dir, "data.yaml")

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

        print(f"✓ YAML: {output_path}")

    def list_tables(self) -> List[str]:
        """Возвращает список всех таблиц в базе данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]

        conn.close()
        return tables


class ConsoleUI:
    def __init__(self):
        self.ticket_system = SupportTicketSystem()
        self.data_exporter = DataExporter()
        self.console_width = 80

    def print_header(self, text: str):
        """Печать заголовка"""
        print("\n" + "=" * self.console_width)
        print(f" {text}".center(self.console_width))
        print("=" * self.console_width)

    def auth_menu(self):
        """Меню авторизации"""
        while True:
            self.print_header("СИСТЕМА УЧЕТА ЗАЯВОК ТЕХПОДДЕРЖКИ")

            print("1. Вход в систему")
            print("2. Регистрация")
            print("3. Выход")

            choice = input("\nВаш выбор (1-3): ").strip()

            if choice == '1':
                if self.login_ui():
                    return True
            elif choice == '2':
                self.register_ui()
            elif choice == '3':
                print("До свидания!")
                return False
            else:
                print("Ошибка: Неверный выбор! Попробуйте снова.")

    def login_ui(self) -> bool:
        """UI для входа в систему"""
        self.print_header("ВХОД В СИСТЕМУ")

        username = input("Логин: ").strip()
        if not username:
            print("Ошибка: Логин не может быть пустым!")
            return False

        password = input("Пароль: ").strip()
        if not password:
            print("Ошибка: Пароль не может быть пустым!")
            return False

        user = self.ticket_system.authenticate_user(username, password)
        if user:
            self.ticket_system.current_user = user
            print(
                f"\nУспешный вход! Добро пожаловать, {user[3]} ({'Специалист поддержки' if user[2] == 'support' else 'Пользователь'})")
            return True
        else:
            print("\nОшибка: Неверный логин или пароль!")
            return False

    def register_ui(self):
        """UI для регистрации"""
        self.print_header("РЕГИСТРАЦИЯ")

        username = input("Логин: ").strip()
        if not username:
            print("Ошибка: Логин не может быть пустым!")
            return

        password = input("Пароль: ").strip()
        if len(password) < 4:
            print("Ошибка: Пароль должен содержать минимум 4 символа!")
            return

        confirm_password = input("Подтвердите пароль: ").strip()
        if password != confirm_password:
            print("Ошибка: Пароли не совпадают!")
            return

        full_name = input("ФИО: ").strip()
        if not full_name:
            print("Ошибка: ФИО не может быть пустым!")
            return

        if self.ticket_system.register_user(username, password, full_name):
            print("\nРегистрация успешна! Теперь вы можете войти в систему.")
        else:
            print("\nОшибка: Пользователь с таким логином уже существует!")

    def print_user_info(self):
        """Печать информации о текущем пользователе"""
        if self.ticket_system.current_user:
            user_id, username, role, full_name = self.ticket_system.current_user
            role_display = "Специалист поддержки" if role == 'support' else "Пользователь"
            print(f"Пользователь: {full_name} ({role_display})")

    def wrap_text(self, text: str, width: int) -> List[str]:
        """Разбивает текст на строки заданной ширины"""
        lines = []
        for paragraph in text.split('\n'):
            if paragraph.strip():
                wrapped = textwrap.wrap(paragraph, width=width)
                lines.extend(wrapped)
            else:
                lines.append('')
        return lines

    def print_ticket_card(self, ticket: Tuple):
        """Печать карточки заявки в псевдографическом стиле"""
        id, title, description, status, priority, created_by, assigned_to, created_at, updated_at = ticket

        # Символы для статусов
        status_symbols = {
            'open': '[O]',
            'in_progress': '[P]',
            'closed': '[C]',
            'resolved': '[R]'
        }

        # Символы для приоритетов
        priority_symbols = {
            'high': '!!!',
            'medium': '!!',
            'low': '!'
        }

        status_symbol = status_symbols.get(status, '[ ]')
        priority_symbol = priority_symbols.get(priority, '!')

        created = datetime.datetime.fromisoformat(created_at).strftime("%d.%m.%Y %H:%M")
        updated = datetime.datetime.fromisoformat(updated_at).strftime("%d.%m.%Y %H:%M")

        content_width = self.console_width - 4  # минус границы

        print(f"┌{'─' * (self.console_width - 2)}┐")

        # Заголовок с ID, статусом и приоритетом
        header_line = f"ID: #{id:04d} {status_symbol} {status.upper():<12} {priority_symbol} {priority.upper():<8}"
        print(f"│ {header_line.ljust(content_width)} │")
        print(f"├{'─' * (self.console_width - 2)}┤")

        # Автор и назначенный специалист
        author_line = f"Автор: {created_by}"
        if assigned_to:
            author_line += f" | Назначен: {assigned_to}"
        print(f"│ {author_line.ljust(content_width)} │")
        print(f"├{'─' * (self.console_width - 2)}┤")

        # Заголовок заявки
        title_line = f"Заголовок: {title}"
        title_lines = self.wrap_text(title_line, content_width)
        for line in title_lines:
            print(f"│ {line.ljust(content_width)} │")

        print(f"├{'─' * (self.console_width - 2)}┤")

        # Описание
        desc_lines = self.wrap_text(description, content_width)
        if desc_lines:
            print(f"│ {'ОПИСАНИЕ:'.ljust(content_width)} │")
            print(f"├{'─' * (self.console_width - 2)}┤")
            for line in desc_lines:
                print(f"│ {line.ljust(content_width)} │")

        print(f"├{'─' * (self.console_width - 2)}┤")

        # Даты
        print(f"│ Создана:  {created.ljust(content_width - 10)} │")
        print(f"│ Обновлена: {updated.ljust(content_width - 11)} │")
        print(f"└{'─' * (self.console_width - 2)}┘")

    def truncate_text(self, text: str, max_length: int) -> str:
        """Обрезает текст до максимальной длины"""
        if len(text) <= max_length:
            return text
        return text[:max_length - 2] + ".."

    def print_tickets_table(self, tickets: List[Tuple]):
        """Печать таблицы заявок"""
        if not tickets:
            print("Нет заявок для отображения")
            return

        # Ширины колонок (фиксированные)
        col_id = 6  # "ID"
        col_title = 25  # "ЗАГОЛОВОК"
        col_status = 12  # "СТАТУС"
        col_priority = 10  # "ПРИОРИТЕТ"
        col_author = 25  # "АВТОР"

        # Общая ширина таблицы
        total_width = col_id + col_title + col_status + col_priority + col_author + 4

        # Верхняя граница
        print(
            "┌" + "─" * col_id + "┬" + "─" * col_title + "┬" + "─" * col_status + "┬" + "─" * col_priority + "┬" + "─" * col_author + "┐")

        # Заголовки
        header_id = "ID"
        header_title = "ЗАГОЛОВОК"
        header_status = "СТАТУС"
        header_priority = "ПРИОР."
        header_author = "АВТОР"

        print(
            f"│ {header_id:^{col_id - 2}} │ {header_title:^{col_title - 2}} │ {header_status:^{col_status - 2}} │ {header_priority:^{col_priority - 2}} │ {header_author:^{col_author - 2}} │")

        # Разделитель
        print(
            "├" + "─" * col_id + "┼" + "─" * col_title + "┼" + "─" * col_status + "┼" + "─" * col_priority + "┼" + "─" * col_author + "┤")

        # Данные
        for ticket in tickets:
            id, title, _, status, priority, created_by, _, _, _ = ticket

            # Форматируем данные с обрезанием
            id_str = str(id)
            title_str = self.truncate_text(title, col_title - 2)
            status_str = self.format_status(status)
            priority_str = self.format_priority(priority)
            author_str = self.truncate_text(created_by, col_author - 2)

            # Выводим строку с фиксированными ширинами
            print(
                f"│ {id_str:^{col_id - 2}} │ {title_str:<{col_title - 2}} │ {status_str:^{col_status - 2}} │ {priority_str:^{col_priority - 2}} │ {author_str:<{col_author - 2}} │")

        # Нижняя граница
        print(
            "└" + "─" * col_id + "┴" + "─" * col_title + "┴" + "─" * col_status + "┴" + "─" * col_priority + "┴" + "─" * col_author + "┘")

    def format_status(self, status: str) -> str:
        """Форматирование статуса для таблицы"""
        status_map = {
            'open': 'ОТКР',
            'in_progress': 'РАБОТА',
            'closed': 'ЗАКР',
            'resolved': 'РЕШЕНА'
        }
        return status_map.get(status, status.upper()[:6])

    def format_priority(self, priority: str) -> str:
        """Форматирование приоритета для таблицы"""
        priority_map = {
            'high': 'ВЫС',
            'medium': 'СРЕД',
            'low': 'НИЗ'
        }
        return priority_map.get(priority, priority.upper()[:4])

    def add_ticket_ui(self):
        """UI для добавления новой заявки"""
        self.print_header("ДОБАВЛЕНИЕ НОВОЙ ЗАЯВКИ")

        title = input("Введите заголовок заявки: ").strip()
        if not title:
            print("Ошибка: Заголовок не может быть пустым!")
            return

        print("Введите описание проблемы (для завершения введите пустую строку):")
        description_lines = []
        while True:
            line = input().strip()
            if not line:
                break
            description_lines.append(line)

        description = "\n".join(description_lines)
        if not description:
            print("Ошибка: Описание не может быть пустым!")
            return

        print("\nВыберите приоритет:")
        print("1. Высокий")
        print("2. Средний")
        print("3. Низкий")

        priority_choice = input("Ваш выбор (1-3, по умолчанию 2): ").strip()
        priorities = {'1': 'high', '2': 'medium', '3': 'low'}
        priority = priorities.get(priority_choice, 'medium')

        try:
            ticket_id = self.ticket_system.add_ticket(title, description, priority)
            print(f"Заявка #{ticket_id} успешно создана!")
        except Exception as e:
            print(f"Ошибка при создании заявки: {e}")

    def view_tickets_ui(self):
        """UI для просмотра заявок"""
        tickets = self.ticket_system.get_all_tickets()

        self.print_header("СПИСОК ЗАЯВОК")
        self.print_tickets_table(tickets)

        if tickets:
            print("\nДействия:")
            print("1. Просмотреть заявку подробно")
            if self.ticket_system.current_user[2] == 'support':
                print("2. Назначить заявку на себя")
            print("3. Назад в меню")

            choice = input("Ваш выбор: ").strip()
            if choice == '1':
                self.view_single_ticket_ui()
            elif choice == '2' and self.ticket_system.current_user[2] == 'support':
                self.assign_ticket_ui()

    def view_single_ticket_ui(self):
        """UI для просмотра одной заявки"""
        try:
            ticket_id = int(input("Введите ID заявки для просмотра: "))
        except ValueError:
            print("Ошибка: Неверный формат ID!")
            return

        ticket = self.ticket_system.get_ticket(ticket_id)
        if not ticket:
            print(f"Ошибка: Заявка #{ticket_id} не найдена!")
            return

        self.print_header(f"ЗАЯВКА #{ticket_id}")
        self.print_ticket_card(ticket)

        print("\nДействия:")
        if self.ticket_system.current_user[2] == 'support':
            print("1. Изменить статус")
            print("2. Назначить на себя")
        print("3. Удалить заявку")
        print("4. Назад к списку")

        choice = input("Ваш выбор: ").strip()

        if choice == '1' and self.ticket_system.current_user[2] == 'support':
            self.change_status_ui(ticket_id)
        elif choice == '2' and self.ticket_system.current_user[2] == 'support':
            self.assign_ticket_to_self(ticket_id)
        elif choice == '3':
            self.delete_ticket_ui(ticket_id)

    def change_status_ui(self, ticket_id: int):
        """UI для изменения статуса заявки"""
        print("\nВыберите новый статус:")
        print("1. Открыта")
        print("2. В работе")
        print("3. Решена")
        print("4. Закрыта")

        status_choice = input("Ваш выбор (1-4): ").strip()
        status_map = {'1': 'open', '2': 'in_progress', '3': 'resolved', '4': 'closed'}

        if status_choice in status_map:
            new_status = status_map[status_choice]
            self.ticket_system.update_ticket_status(ticket_id, new_status)
            print(f"Статус заявки #{ticket_id} изменен на '{new_status}'")
        else:
            print("Ошибка: Неверный выбор!")

    def assign_ticket_ui(self):
        """UI для назначения заявки"""
        try:
            ticket_id = int(input("Введите ID заявки для назначения: "))
        except ValueError:
            print("Ошибка: Неверный формат ID!")
            return

        self.assign_ticket_to_self(ticket_id)

    def assign_ticket_to_self(self, ticket_id: int):
        """Назначение заявки на текущего пользователя"""
        try:
            self.ticket_system.assign_ticket(ticket_id, self.ticket_system.current_user[0])
            print(f"Заявка #{ticket_id} назначена на вас!")
        except Exception as e:
            print(f"Ошибка: {e}")

    def delete_ticket_ui(self, ticket_id: int):
        """UI для удаления заявки"""
        confirm = input(f"Вы уверены, что хотите удалить заявку #{ticket_id}? (y/N): ").strip().lower()
        if confirm == 'y':
            try:
                self.ticket_system.delete_ticket(ticket_id)
                print(f"Заявка #{ticket_id} удалена!")
            except Exception as e:
                print(f"Ошибка при удалении: {e}")
        else:
            print("Удаление отменено")

    def show_statistics(self):
        """Показ статистики"""
        tickets = self.ticket_system.get_all_tickets()

        status_count = {}
        priority_count = {}

        for ticket in tickets:
            status = ticket[3]
            priority = ticket[4]

            status_count[status] = status_count.get(status, 0) + 1
            priority_count[priority] = priority_count.get(priority, 0) + 1

        self.print_header("СТАТИСТИКА")

        print("По статусам:")
        for status, count in status_count.items():
            status_display = self.format_status(status).ljust(6)
            print(f"   {status_display}: {count}")

        print("\nПо приоритетам:")
        for priority, count in priority_count.items():
            priority_display = self.format_priority(priority).ljust(4)
            print(f"   {priority_display}: {count}")

        print(f"\nВсего заявок: {len(tickets)}")

    def export_data_ui(self):
        """UI для экспорта данных"""
        if self.ticket_system.current_user[2] != 'support':
            print("Ошибка: Экспорт данных доступен только для специалистов поддержки!")
            return

        self.print_header("ЭКСПОРТ ДАННЫХ")

        # Показываем доступные таблицы
        tables = self.data_exporter.list_tables()
        print("Доступные таблицы в базе данных:")
        for i, table in enumerate(tables, 1):
            print(f"{i}. {table}")

        # Выбираем таблицу для экспорта
        while True:
            try:
                choice = input("\nВыберите номер таблицы для экспорта: ").strip()
                if not choice:
                    table_name = "tickets"  # таблица по умолчанию
                    break

                table_index = int(choice) - 1
                if 0 <= table_index < len(tables):
                    table_name = tables[table_index]
                    break
                else:
                    print("Неверный номер таблицы!")
            except ValueError:
                print("Введите корректный номер!")

        # Экспортируем данные
        try:
            self.data_exporter.export_table_data(table_name)
        except Exception as e:
            print(f"Ошибка при экспорте: {e}")

    def main_menu(self):
        """Главное меню"""
        while True:
            self.print_header("СИСТЕМА УЧЕТА ЗАЯВОК ТЕХПОДДЕРЖКИ")
            self.print_user_info()
            print()

            menu_items = [
                "1. Создать новую заявку",
                "2. Просмотреть все заявки",
                "3. Показать статистику"
            ]

            # Добавляем пункт экспорта только для саппортов
            if self.ticket_system.current_user[2] == 'support':
                menu_items.append("4. Экспорт данных")
                menu_items.append("5. Выйти из системы")
            else:
                menu_items.append("4. Выйти из системы")

            for item in menu_items:
                print(item)

            choice = input("\nВаш выбор: ").strip()

            if choice == '1':
                self.add_ticket_ui()
            elif choice == '2':
                self.view_tickets_ui()
            elif choice == '3':
                self.show_statistics()
            elif choice == '4' and self.ticket_system.current_user[2] == 'support':
                self.export_data_ui()
            elif (choice == '4' and self.ticket_system.current_user[2] != 'support') or \
                    (choice == '5' and self.ticket_system.current_user[2] == 'support'):
                self.ticket_system.current_user = None
                print("Выход из системы выполнен.")
                break
            else:
                print("Ошибка: Неверный выбор! Попробуйте снова.")

            input("\nНажмите Enter для продолжения...")

    def run(self):
        """Запуск приложения"""
        while True:
            if self.auth_menu():
                self.main_menu()
            else:
                break


def main():
    """Основная функция"""
    ui = ConsoleUI()
    ui.run()


if __name__ == "__main__":
    main()