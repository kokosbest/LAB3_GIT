import sqlite3
import datetime
from typing import List, Tuple, Optional


class SupportTicketSystem:
    def __init__(self, db_name: str = "support_tickets.db"):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        """Инициализация базы данных и создание таблицы"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                priority TEXT NOT NULL DEFAULT 'medium',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        conn.commit()
        conn.close()

    def add_ticket(self, title: str, description: str, priority: str = "medium") -> int:
        """Добавление новой заявки"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        current_time = datetime.datetime.now().isoformat()

        cursor.execute('''
            INSERT INTO tickets (title, description, priority, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, description, priority, current_time, current_time))

        ticket_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return ticket_id

    def get_all_tickets(self) -> List[Tuple]:
        """Получение всех заявок"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, title, description, status, priority, created_at, updated_at
            FROM tickets
            ORDER BY 
                CASE priority 
                    WHEN 'high' THEN 1
                    WHEN 'medium' THEN 2
                    WHEN 'low' THEN 3
                END,
                created_at DESC
        ''')

        tickets = cursor.fetchall()
        conn.close()

        return tickets

    def get_ticket(self, ticket_id: int) -> Optional[Tuple]:
        """Получение конкретной заявки по ID"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, title, description, status, priority, created_at, updated_at
            FROM tickets WHERE id = ?
        ''', (ticket_id,))

        ticket = cursor.fetchone()
        conn.close()

        return ticket

    def update_ticket_status(self, ticket_id: int, status: str):
        """Обновление статуса заявки"""
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

    def delete_ticket(self, ticket_id: int):
        """Удаление заявки"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM tickets WHERE id = ?', (ticket_id,))

        conn.commit()
        conn.close()


class ConsoleUI:
    def __init__(self):
        self.ticket_system = SupportTicketSystem()

    def print_header(self, text: str):
        """Печать заголовка"""
        print("\n" + "=" * 60)
        print(f" {text}".center(60))
        print("=" * 60)

    def print_separator(self):
        """Печать разделителя"""
        print("-" * 60)

    def print_ticket_card(self, ticket: Tuple):
        """Печать карточки заявки в псевдографическом стиле"""
        id, title, description, status, priority, created_at, updated_at = ticket

        # Цвета для статусов
        status_colors = {
            'open': '🟢',
            'in_progress': '🟡',
            'closed': '🔴',
            'resolved': '🟣'
        }

        # Цвета для приоритетов
        priority_colors = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }

        status_icon = status_colors.get(status, '⚪')
        priority_icon = priority_colors.get(priority, '⚪')

        created = datetime.datetime.fromisoformat(created_at).strftime("%d.%m.%Y %H:%M")
        updated = datetime.datetime.fromisoformat(updated_at).strftime("%d.%m.%Y %H:%M")

        print(f"┌{'─' * 58}┐")
        print(f"│ #{id:04d} {status_icon} {status.upper():<12} {priority_icon} {priority.upper():<8} │")
        print(f"├{'─' * 58}┤")
        print(f"│ {title:<56} │")
        print(f"├{'─' * 58}┤")

        # Разбиваем описание на строки по 56 символов
        desc_lines = []
        current_line = ""
        for word in description.split():
            if len(current_line + " " + word) <= 56:
                current_line += " " + word if current_line else word
            else:
                desc_lines.append(current_line)
                current_line = word
        if current_line:
            desc_lines.append(current_line)

        for line in desc_lines:
            print(f"│ {line:<56} │")

        print(f"├{'─' * 58}┤")
        print(f"│  Создана: {created:<44} │")
        print(f"│  Обновлена: {updated:<42} │")
        print(f"└{'─' * 58}┘")

    def print_tickets_table(self, tickets: List[Tuple]):
        """Печать таблицы заявок"""
        if not tickets:
            print(" Нет заявок для отображения")
            return

        print(f"┌{'─' * 4}┬{'─' * 30}┬{'─' * 10}┬{'─' * 12}┐")
        print(f"│ {'ID':<2} │ {'ЗАГОЛОВОК':<28} │ {'СТАТУС':<8} │ {'ПРИОРИТЕТ':<10} │")
        print(f"├{'─' * 4}┼{'─' * 30}┼{'─' * 10}┼{'─' * 12}┤")

        for ticket in tickets:
            id, title, _, status, priority, _, _ = ticket

            # Обрезаем длинные заголовки
            display_title = title[:28] + "..." if len(title) > 28 else title

            status_icons = {'open': '🟢', 'in_progress': '🟡', 'closed': '🔴', 'resolved': '🟣'}
            priority_icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}

            status_display = f"{status_icons.get(status, '⚪')} {status}"
            priority_display = f"{priority_icons.get(priority, '⚪')} {priority}"

            print(f"│ {id:>2} │ {display_title:<28} │ {status_display:<8} │ {priority_display:<10} │")

        print(f"└{'─' * 4}┴{'─' * 30}┴{'─' * 10}┴{'─' * 12}┘")

    def add_ticket_ui(self):
        """UI для добавления новой заявки"""
        self.print_header(" ДОБАВЛЕНИЕ НОВОЙ ЗАЯВКИ")

        title = input("Введите заголовок заявки: ").strip()
        if not title:
            print(" Заголовок не может быть пустым!")
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
            print(" Описание не может быть пустым!")
            return

        print("\nВыберите приоритет:")
        print("1. 🔴 Высокий")
        print("2. 🟡 Средний")
        print("3. 🟢 Низкий")

        priority_choice = input("Ваш выбор (1-3, по умолчанию 2): ").strip()
        priorities = {'1': 'high', '2': 'medium', '3': 'low'}
        priority = priorities.get(priority_choice, 'medium')

        ticket_id = self.ticket_system.add_ticket(title, description, priority)
        print(f" Заявка #{ticket_id} успешно создана!")

    def view_tickets_ui(self):
        """UI для просмотра заявок"""
        tickets = self.ticket_system.get_all_tickets()

        self.print_header(" СПИСОК ЗАЯВОК")
        self.print_tickets_table(tickets)

        if tickets:
            print("\nДействия:")
            print("1.  Просмотреть заявку подробно")
            print("2. ↩  Назад в меню")

            choice = input("Ваш выбор: ").strip()
            if choice == '1':
                self.view_single_ticket_ui()

    def view_single_ticket_ui(self):
        """UI для просмотра одной заявки"""
        try:
            ticket_id = int(input("Введите ID заявки для просмотра: "))
        except ValueError:
            print(" Неверный формат ID!")
            return

        ticket = self.ticket_system.get_ticket(ticket_id)
        if not ticket:
            print(f" Заявка #{ticket_id} не найдена!")
            return

        self.print_header(f"📄 ЗАЯВКА #{ticket_id}")
        self.print_ticket_card(ticket)

        print("\nДействия:")
        print("1.   Изменить статус")
        print("2.   Удалить заявку")
        print("3.   Назад к списку")

        choice = input("Ваш выбор: ").strip()

        if choice == '1':
            self.change_status_ui(ticket_id)
        elif choice == '2':
            self.delete_ticket_ui(ticket_id)

    def change_status_ui(self, ticket_id: int):
        """UI для изменения статуса заявки"""
        print("\nВыберите новый статус:")
        print("1. 🟢 Открыта")
        print("2. 🟡 В работе")
        print("3. 🟣 Решена")
        print("4. 🔴 Закрыта")

        status_choice = input("Ваш выбор (1-4): ").strip()
        status_map = {'1': 'open', '2': 'in_progress', '3': 'resolved', '4': 'closed'}

        if status_choice in status_map:
            new_status = status_map[status_choice]
            self.ticket_system.update_ticket_status(ticket_id, new_status)
            print(f" Статус заявки #{ticket_id} изменен на '{new_status}'")
        else:
            print(" Неверный выбор!")

    def delete_ticket_ui(self, ticket_id: int):
        """UI для удаления заявки"""
        confirm = input(f" Вы уверены, что хотите удалить заявку #{ticket_id}? (y/N): ").strip().lower()
        if confirm == 'y':
            self.ticket_system.delete_ticket(ticket_id)
            print(f" Заявка #{ticket_id} удалена!")
        else:
            print(" Удаление отменено")

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

        self.print_header(" СТАТИСТИКА")

        print(" По статусам:")
        for status, count in status_count.items():
            status_icons = {'open': '🟢', 'in_progress': '🟡', 'closed': '🔴', 'resolved': '🟣'}
            print(f"   {status_icons.get(status, '⚪')} {status}: {count}")

        print("\n По приоритетам:")
        for priority, count in priority_count.items():
            priority_icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
            print(f"   {priority_icons.get(priority, '⚪')} {priority}: {count}")

        print(f"\n Всего заявок: {len(tickets)}")

    def main_menu(self):
        """Главное меню"""
        while True:
            self.print_header(" СИСТЕМА УЧЕТА ЗАЯВОК ТЕХПОДДЕРЖКИ")

            print("1.  Создать новую заявку")
            print("2.  Просмотреть все заявки")
            print("3.  Показать статистику")
            print("4.  Выход")

            choice = input("\nВаш выбор (1-4): ").strip()

            if choice == '1':
                self.add_ticket_ui()
            elif choice == '2':
                self.view_tickets_ui()
            elif choice == '3':
                self.show_statistics()
            elif choice == '4':
                print(" До свидания!")
                break
            else:
                print(" Неверный выбор! Попробуйте снова.")

            input("\nНажмите Enter для продолжения...")


def main():
    """Основная функция"""
    ui = ConsoleUI()
    ui.main_menu()


if __name__ == "__main__":
    main()