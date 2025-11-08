# Логика работы с заявками
import sqlite3
import datetime
from typing import List, Optional
from database.connection import DatabaseConnection
from database.models import Ticket, TicketWithRelations


class TicketSystem:
    def __init__(self, db_connection: DatabaseConnection, auth_manager):
        self.db_connection = db_connection
        self.auth_manager = auth_manager

    def add_ticket(self, title: str, description: str, priority: str = "medium") -> int:
        """Добавление новой заявки"""
        if not self.auth_manager.is_authenticated():
            raise Exception("Пользователь не аутентифицирован")

        conn = self.db_connection.get_connection()
        cursor = conn.cursor()

        current_time = datetime.datetime.now().isoformat()

        cursor.execute('''
            INSERT INTO tickets (title, description, priority, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, description, priority, self.auth_manager.current_user.id, current_time, current_time))

        ticket_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return ticket_id

    def get_all_tickets(self) -> List[TicketWithRelations]:
        """Получение всех заявок"""
        conn = self.db_connection.get_connection()
        cursor = conn.cursor()

        if self.auth_manager.is_support():
            # Саппорт видит все заявки
            cursor.execute('''
                SELECT t.id, t.title, t.description, t.status, t.priority, 
                       t.created_by, t.assigned_to, t.created_at, t.updated_at,
                       u1.full_name as created_by_name, u2.full_name as assigned_to_name
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
                       t.created_by, t.assigned_to, t.created_at, t.updated_at,
                       u1.full_name as created_by_name, u2.full_name as assigned_to_name
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
            ''', (self.auth_manager.current_user.id,))

        tickets_data = cursor.fetchall()
        conn.close()

        tickets = []
        for ticket_data in tickets_data:
            tickets.append(TicketWithRelations(*ticket_data))

        return tickets

    def get_ticket(self, ticket_id: int) -> Optional[TicketWithRelations]:
        """Получение конкретной заявки по ID"""
        conn = self.db_connection.get_connection()
        cursor = conn.cursor()

        if self.auth_manager.is_support():
            cursor.execute('''
                SELECT t.id, t.title, t.description, t.status, t.priority, 
                       t.created_by, t.assigned_to, t.created_at, t.updated_at,
                       u1.full_name as created_by_name, u2.full_name as assigned_to_name
                FROM tickets t
                LEFT JOIN users u1 ON t.created_by = u1.id
                LEFT JOIN users u2 ON t.assigned_to = u2.id
                WHERE t.id = ?
            ''', (ticket_id,))
        else:
            cursor.execute('''
                SELECT t.id, t.title, t.description, t.status, t.priority, 
                       t.created_by, t.assigned_to, t.created_at, t.updated_at,
                       u1.full_name as created_by_name, u2.full_name as assigned_to_name
                FROM tickets t
                LEFT JOIN users u1 ON t.created_by = u1.id
                LEFT JOIN users u2 ON t.assigned_to = u2.id
                WHERE t.id = ? AND t.created_by = ?
            ''', (ticket_id, self.auth_manager.current_user.id))

        ticket_data = cursor.fetchone()
        conn.close()

        if ticket_data:
            return TicketWithRelations(*ticket_data)
        return None

    def update_ticket_status(self, ticket_id: int, status: str):
        """Обновление статуса заявки"""
        if not self.auth_manager.is_authenticated():
            raise Exception("Пользователь не аутентифицирован")

        conn = self.db_connection.get_connection()
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
        if not self.auth_manager.is_support():
            raise Exception("Только саппорт может назначать заявки")

        conn = self.db_connection.get_connection()
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
        if not self.auth_manager.is_authenticated():
            raise Exception("Пользователь не аутентифицирован")

        conn = self.db_connection.get_connection()
        cursor = conn.cursor()

        if self.auth_manager.is_support():
            cursor.execute('DELETE FROM tickets WHERE id = ?', (ticket_id,))
        else:
            cursor.execute('DELETE FROM tickets WHERE id = ? AND created_by = ?',
                           (ticket_id, self.auth_manager.current_user.id))

        conn.commit()
        conn.close()