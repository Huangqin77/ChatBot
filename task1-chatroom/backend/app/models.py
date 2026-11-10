from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field


def uid() -> str:
    return uuid4().hex


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class User(SQLModel, table=True):
    __tablename__ = 'users'
    id: str = Field(default_factory=uid, primary_key=True)
    nickname: str
    token: str = Field(default_factory=uid, unique=True, index=True)
    created_at: str = Field(default_factory=now)


class Room(SQLModel, table=True):
    __tablename__ = 'rooms'
    id: str = Field(default_factory=uid, primary_key=True)
    name: str
    description: str = ''
    created_at: str = Field(default_factory=now)


class Bot(SQLModel, table=True):
    __tablename__ = 'bots'
    id: str = Field(default_factory=uid, primary_key=True)
    name: str = Field(unique=True, index=True)
    role: str
    system_prompt: str
    tools: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: str = Field(default_factory=now)


class RoomBot(SQLModel, table=True):
    __tablename__ = 'room_bots'
    room_id: str = Field(foreign_key='rooms.id', primary_key=True)
    bot_id: str = Field(foreign_key='bots.id', primary_key=True)


class Message(SQLModel, table=True):
    __tablename__ = 'messages'
    id: str = Field(default_factory=uid, primary_key=True)
    room_id: str = Field(foreign_key='rooms.id', index=True)
    kind: str  # user | bot | system
    sender_id: str | None = None
    sender_name: str
    content: str
    task_id: str | None = Field(default=None, foreign_key='tasks.id')
    mode: str | None = None
    client_id: str | None = Field(default=None, unique=True)
    created_at: str = Field(default_factory=now, index=True)


class Task(SQLModel, table=True):
    __tablename__ = 'tasks'
    id: str = Field(default_factory=uid, primary_key=True)
    room_id: str = Field(foreign_key='rooms.id', index=True)
    bot_id: str = Field(foreign_key='bots.id')
    bot_name: str
    parent_id: str | None = Field(default=None, foreign_key='tasks.id')
    root_id: str = Field(index=True)
    trigger_message_id: str = Field(foreign_key='messages.id')
    depth: int = 0
    status: str = 'running'
    mode: str
    input: str
    output: str = ''
    error: str | None = None
    created_at: str = Field(default_factory=now)
    completed_at: str | None = None


class ToolCall(SQLModel, table=True):
    __tablename__ = 'tool_calls'
    id: str = Field(default_factory=uid, primary_key=True)
    room_id: str = Field(foreign_key='rooms.id', index=True)
    task_id: str = Field(foreign_key='tasks.id', index=True)
    root_id: str = Field(index=True)
    name: str
    input: dict = Field(default_factory=dict, sa_column=Column(JSON))
    provider_call_id: str | None = None  # Original model tool_call_id; None for Demo.
    output: str = ''
    status: str = 'running'
    child_task_id: str | None = Field(default=None, foreign_key='tasks.id')
    created_at: str = Field(default_factory=now)
    completed_at: str | None = None
