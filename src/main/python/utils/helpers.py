# Вспомогательные функции
import datetime
from typing import Any

def format_datetime(dt_string: str) -> str:
    """Форматирование даты и времени"""
    try:
        dt = datetime.datetime.fromisoformat(dt_string)
        return dt.strftime("%d.%m.%Y %H:%M")
    except:
        return dt_string

def safe_get(dictionary: dict, key: str, default: Any = None) -> Any:
    """Безопасное получение значения из словаря"""
    return dictionary.get(key, default)