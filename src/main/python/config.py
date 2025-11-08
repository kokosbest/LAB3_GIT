# Конфигурация приложения
import os


class Config:
    DB_NAME = "support_tickets.db"
    OUTPUT_DIR = "out"
    CONSOLE_WIDTH = 80

    # Настройки отображения
    STATUS_SYMBOLS = {
        'open': '[O]',
        'in_progress': '[P]',
        'closed': '[C]',
        'resolved': '[R]'
    }

    PRIORITY_SYMBOLS = {
        'high': '!!!',
        'medium': '!!',
        'low': '!'
    }

    # Ширины колонок для таблицы
    COLUMN_WIDTHS = {
        'id': 6,
        'title': 25,
        'status': 12,
        'priority': 10,
        'author': 25
    }