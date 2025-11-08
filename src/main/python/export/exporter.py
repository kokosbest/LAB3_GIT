# Экспорт данных в различные форматы
import sqlite3
import json
import csv
import xml.etree.ElementTree as ET
import yaml
import os
from typing import List, Dict, Any
from database.connection import DatabaseConnection
from config import Config


class DataExporter:
    """Класс для экспорта данных в различные форматы"""

    def __init__(self, db_connection: DatabaseConnection):
        self.db_connection = db_connection
        self.output_dir = Config.OUTPUT_DIR
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        """Создает папку out, если её нет"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def get_table_structure(self, table_name: str) -> List[Dict[str, str]]:
        """Получает структуру таблицы"""
        conn = self.db_connection.get_connection()
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
        conn = self.db_connection.get_connection()
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
        conn = self.db_connection.get_connection()
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
        conn = self.db_connection.get_connection()
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
        conn = self.db_connection.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]

        conn.close()
        return tables