# Главный файл для запуска приложения
from ui.console_ui import ConsoleUI

def main():
    """Основная функция"""
    print("Запуск системы учета заявок техподдержки...")
    ui = ConsoleUI()
    ui.run()

if __name__ == "__main__":
    main()