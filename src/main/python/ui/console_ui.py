# Консольный интерфейс пользователя
import getpass
from typing import List
from database.connection import DatabaseConnection
from core.auth import AuthManager
from core.ticket_system import TicketSystem
from export.exporter import DataExporter
from ui.display import DisplayManager
from database.models import User, TicketWithRelations


class ConsoleUI:
    def __init__(self):
        self.db_connection = DatabaseConnection()
        self.auth_manager = AuthManager(self.db_connection)
        self.ticket_system = TicketSystem(self.db_connection, self.auth_manager)
        self.data_exporter = DataExporter(self.db_connection)
        self.display = DisplayManager()

        # Инициализация базы данных
        self.db_connection.init_database()

    def auth_menu(self):
        """Меню авторизации"""
        while True:
            self.display.print_header("СИСТЕМА УЧЕТА ЗАЯВОК ТЕХПОДДЕРЖКИ")

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
        self.display.print_header("ВХОД В СИСТЕМУ")

        username = input("Логин: ").strip()
        if not username:
            print("Ошибка: Логин не может быть пустым!")
            return False

        password = input("Пароль: ").strip()
        if not password:
            print("Ошибка: Пароль не может быть пустым!")
            return False

        if self.auth_manager.login(username, password):
            user = self.auth_manager.current_user
            role_display = "Специалист поддержки" if user.role == 'support' else "Пользователь"
            print(f"\nУспешный вход! Добро пожаловать, {user.full_name} ({role_display})")
            return True
        else:
            print("\nОшибка: Неверный логин или пароль!")
            return False

    def register_ui(self):
        """UI для регистрации"""
        self.display.print_header("РЕГИСТРАЦИЯ")

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

        if self.auth_manager.register_user(username, password, full_name):
            print("\nРегистрация успешна! Теперь вы можете войти в систему.")
        else:
            print("\nОшибка: Пользователь с таким логином уже существует!")

    def print_user_info(self):
        """Печать информации о текущем пользователе"""
        if self.auth_manager.is_authenticated():
            user = self.auth_manager.current_user
            role_display = "Специалист поддержки" if user.role == 'support' else "Пользователь"
            print(f"Пользователь: {user.full_name} ({role_display})")

    def add_ticket_ui(self):
        """UI для добавления новой заявки"""
        self.display.print_header("ДОБАВЛЕНИЕ НОВОЙ ЗАЯВКИ")

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

        self.display.print_header("СПИСОК ЗАЯВОК")
        self.display.print_tickets_table(tickets)

        if tickets:
            print("\nДействия:")
            print("1. Просмотреть заявку подробно")
            if self.auth_manager.is_support():
                print("2. Назначить заявку на себя")
            print("3. Назад в меню")

            choice = input("Ваш выбор: ").strip()
            if choice == '1':
                self.view_single_ticket_ui()
            elif choice == '2' and self.auth_manager.is_support():
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

        self.display.print_header(f"ЗАЯВКА #{ticket_id}")
        self.display.print_ticket_card(ticket)

        print("\nДействия:")
        if self.auth_manager.is_support():
            print("1. Изменить статус")
            print("2. Назначить на себя")
        print("3. Удалить заявку")
        print("4. Назад к списку")

        choice = input("Ваш выбор: ").strip()

        if choice == '1' and self.auth_manager.is_support():
            self.change_status_ui(ticket_id)
        elif choice == '2' and self.auth_manager.is_support():
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
            self.ticket_system.assign_ticket(ticket_id, self.auth_manager.current_user.id)
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
            status_count[ticket.status] = status_count.get(ticket.status, 0) + 1
            priority_count[ticket.priority] = priority_count.get(ticket.priority, 0) + 1

        self.display.print_header("СТАТИСТИКА")

        print("По статусам:")
        for status, count in status_count.items():
            status_display = self.display.format_status(status).ljust(6)
            print(f"   {status_display}: {count}")

        print("\nПо приоритетам:")
        for priority, count in priority_count.items():
            priority_display = self.display.format_priority(priority).ljust(4)
            print(f"   {priority_display}: {count}")

        print(f"\nВсего заявок: {len(tickets)}")

    def export_data_ui(self):
        """UI для экспорта данных"""
        if not self.auth_manager.is_support():
            print("Ошибка: Экспорт данных доступен только для специалистов поддержки!")
            return

        self.display.print_header("ЭКСПОРТ ДАННЫХ")

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
            self.display.print_header("СИСТЕМА УЧЕТА ЗАЯВОК ТЕХПОДДЕРЖКИ")
            self.print_user_info()
            print()

            menu_items = [
                "1. Создать новую заявку",
                "2. Просмотреть все заявки",
                "3. Показать статистику"
            ]

            # Добавляем пункт экспорта только для саппортов
            if self.auth_manager.is_support():
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
            elif choice == '4' and self.auth_manager.is_support():
                self.export_data_ui()
            elif (choice == '4' and not self.auth_manager.is_support()) or \
                    (choice == '5' and self.auth_manager.is_support()):
                self.auth_manager.logout()
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