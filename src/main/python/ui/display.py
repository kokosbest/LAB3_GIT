# Отображение данных в консоли
import textwrap
import datetime
from typing import List, Tuple
from database.models import TicketWithRelations
from config import Config


class DisplayManager:
    def __init__(self):
        self.console_width = Config.CONSOLE_WIDTH

    def print_header(self, text: str):
        """Печать заголовка"""
        print("\n" + "=" * self.console_width)
        print(f" {text}".center(self.console_width))
        print("=" * self.console_width)

    def print_separator(self):
        """Печать разделителя"""
        print("-" * self.console_width)

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

    def print_ticket_card(self, ticket: TicketWithRelations):
        """Печать карточки заявки в псевдографическом стиле"""
        # Символы для статусов и приоритетов
        status_symbol = Config.STATUS_SYMBOLS.get(ticket.status, '[ ]')
        priority_symbol = Config.PRIORITY_SYMBOLS.get(ticket.priority, '!')

        created = datetime.datetime.fromisoformat(ticket.created_at).strftime("%d.%m.%Y %H:%M")
        updated = datetime.datetime.fromisoformat(ticket.updated_at).strftime("%d.%m.%Y %H:%M")

        content_width = self.console_width - 4  # минус границы

        print(f"┌{'─' * (self.console_width - 2)}┐")

        # Заголовок с ID, статусом и приоритетом
        header_line = f"ID: #{ticket.id:04d} {status_symbol} {ticket.status.upper():<12} {priority_symbol} {ticket.priority.upper():<8}"
        print(f"│ {header_line.ljust(content_width)} │")
        print(f"├{'─' * (self.console_width - 2)}┤")

        # Автор и назначенный специалист
        author_line = f"Автор: {ticket.created_by_name}"
        if ticket.assigned_to_name:
            author_line += f" | Назначен: {ticket.assigned_to_name}"
        print(f"│ {author_line.ljust(content_width)} │")
        print(f"├{'─' * (self.console_width - 2)}┤")

        # Заголовок заявки
        title_line = f"Заголовок: {ticket.title}"
        title_lines = self.wrap_text(title_line, content_width)
        for line in title_lines:
            print(f"│ {line.ljust(content_width)} │")

        print(f"├{'─' * (self.console_width - 2)}┤")

        # Описание
        desc_lines = self.wrap_text(ticket.description, content_width)
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

    def print_tickets_table(self, tickets: List[TicketWithRelations]):
        """Печать таблицы заявок"""
        if not tickets:
            print("Нет заявок для отображения")
            return

        widths = Config.COLUMN_WIDTHS

        # Верхняя граница
        print(
            "┌" + "─" * widths['id'] + "┬" + "─" * widths['title'] + "┬" + "─" * widths['status'] + "┬" + "─" * widths[
                'priority'] + "┬" + "─" * widths['author'] + "┐")

        # Заголовки
        headers = ['ID', 'ЗАГОЛОВОК', 'СТАТУС', 'ПРИОР.', 'АВТОР']
        print(
            f"│ {headers[0]:^{widths['id'] - 2}} │ {headers[1]:^{widths['title'] - 2}} │ {headers[2]:^{widths['status'] - 2}} │ {headers[3]:^{widths['priority'] - 2}} │ {headers[4]:^{widths['author'] - 2}} │")

        # Разделитель
        print(
            "├" + "─" * widths['id'] + "┼" + "─" * widths['title'] + "┼" + "─" * widths['status'] + "┼" + "─" * widths[
                'priority'] + "┼" + "─" * widths['author'] + "┤")

        # Данные
        for ticket in tickets:
            # Форматируем данные с обрезанием
            id_str = str(ticket.id)
            title_str = self.truncate_text(ticket.title, widths['title'] - 2)
            status_str = self.format_status(ticket.status)
            priority_str = self.format_priority(ticket.priority)
            author_str = self.truncate_text(ticket.created_by_name or "", widths['author'] - 2)

            # Выводим строку с фиксированными ширинами
            print(
                f"│ {id_str:^{widths['id'] - 2}} │ {title_str:<{widths['title'] - 2}} │ {status_str:^{widths['status'] - 2}} │ {priority_str:^{widths['priority'] - 2}} │ {author_str:<{widths['author'] - 2}} │")

        # Нижняя граница
        print(
            "└" + "─" * widths['id'] + "┴" + "─" * widths['title'] + "┴" + "─" * widths['status'] + "┴" + "─" * widths[
                'priority'] + "┴" + "─" * widths['author'] + "┘")

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