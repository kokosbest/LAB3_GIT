# Модели данных
from dataclasses import dataclass
from typing import Optional
import datetime


@dataclass
class User:
    id: int
    username: str
    role: str
    full_name: str
    created_at: str


@dataclass
class Ticket:
    id: int
    title: str
    description: str
    status: str
    priority: str
    created_by: int
    assigned_to: Optional[int]
    created_at: str
    updated_at: str
    created_by_name: Optional[str] = None
    assigned_to_name: Optional[str] = None


@dataclass
class TicketWithRelations:
    id: int
    title: str
    description: str
    status: str
    priority: str
    created_by: int
    assigned_to: Optional[int]
    created_at: str
    updated_at: str
    created_by_name: Optional[str] = None
    assigned_to_name: Optional[str] = None

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_by': self.created_by,
            'assigned_to': self.assigned_to,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'created_by_name': self.created_by_name,
            'assigned_to_name': self.assigned_to_name
        }