import asyncio
import json
import re
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field as PField, field_validator, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from .agent import AgentRunner
from .config import Settings
from .db import make_engine, initialize
from .hub import Hub
from .models import User, Room, Bot, RoomBot, Message, Task, ToolCall
from .tools import TOOL_NAMES


class LoginInput(BaseModel):
    nickname: str = PField(min_length=1, max_length=24)

    @field_validator('nickname')
    @classmethod
    def clean(cls, value):
        if not value.strip():
            raise ValueError('昵称不能为空')
        return value.strip()


class RoomInput(BaseModel):
    name: str = PField(min_length=1, max_length=40)
    description: str = PField(default='', max_length=240)

    @field_validator('name')
    @classmethod
    def clean(cls, value):
        if not value.strip():
            raise ValueError('房间名称不能为空')
        return value.strip()


class BotInput(BaseModel):
    name: str = PField(min_length=1, max_length=24, pattern=r'^[\w\-]+$')
    role: str = PField(min_length=1, max_length=120)
    system_prompt: str = PField(min_length=1, max_length=6000)
    tools: list[str] = PField(default_factory=list, max_length=3)

    @field_validator('role', 'system_prompt')
    @classmethod
    def clean(cls, value):
        if not value.strip():
            raise ValueError('内容不能为空')
        return value.strip()

    @field_validator('tools')
    @classmethod
    def known_tools(cls, value):
        if set(value) - TOOL_NAMES or len(set(value)) != len(value):
            raise ValueError('工具名称无效或重复')
        return value


class RoomBotsInput(BaseModel):
    bot_ids: list[str] = PField(max_length=30)


class ChatInput(BaseModel):
    content: str = PField(min_length=1, max_length=4000)
    client_id: str = PField(min_length=1, max_length=80)

    @field_validator('content')
    @classmethod
    def clean(cls, value):
        if not value.strip():
            raise ValueError('消息不能为空')
        return value.strip()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    engine, hub = make_engine(settings.database_url), Hub()
    runner = AgentRunner(engine, settings, hub)

    @asynccontextmanager
    async def lifespan(_):
        initialize(engine)
        yield
        await runner.shutdown()
        engine.dispose()

    app = FastAPI(title='Relay · 多人 AI 协作聊天室', lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=settings.origins,
                       allow_credentials=False, allow_methods=['GET', 'POST', 'PUT'], allow_headers=['Authorization', 'Content-Type'])
    app.state.engine, app.state.runner = engine, runner

    def user_by_token(token):
        with Session(engine) as s:
            return s.exec(select(User).where(User.token == token)).first()

    def current_user(authorization: Annotated[str | None, Header()] = None):
        token = (authorization or '').removeprefix('Bearer ')
        user = user_by_token(token)
        if user is None:
            raise HTTPException(401, '请先使用昵称进入系统')
        return user

    def room_or_404(s, room_id):
        room = s.get(Room, room_id)
        if not room:
            raise HTTPException(404, '房间不存在')
        return room

    def recent_messages(s, room_id, before_id=None, limit=100):
        query = select(Message).where(Message.room_id == room_id)
        if before_id:
            cursor = s.get(Message, before_id)
            if not cursor or cursor.room_id != room_id:
                raise HTTPException(404, '历史消息游标不存在')
            query = query.where((Message.created_at < cursor.created_at) |
                                ((Message.created_at == cursor.created_at) & (Message.id < cursor.id)))
        rows = s.exec(query.order_by(Message.created_at.desc(), Message.id.desc()).limit(limit + 1)).all()
        return {'messages': [m.model_dump() for m in reversed(rows[:limit])], 'has_more': len(rows) > limit}

    def snapshot(room_id):
        with Session(engine) as s:
            room = room_or_404(s, room_id)
            roots = s.exec(select(Task.id).where(Task.room_id == room_id, Task.parent_id == None)
                           .order_by(Task.created_at.desc()).limit(50)).all()
            tasks = s.exec(select(Task).where(Task.root_id.in_(roots)).order_by(Task.created_at)).all() if roots else []
            calls = s.exec(select(ToolCall).where(ToolCall.root_id.in_(roots)).order_by(ToolCall.created_at)).all() if roots else []
            bots = s.exec(select(Bot).join(RoomBot).where(RoomBot.room_id == room_id)).all()
            return {'room': room.model_dump(), 'bots': [b.model_dump() for b in bots],
                    **recent_messages(s, room_id), 'tasks': [t.model_dump() for t in tasks],
                    'tool_calls': [t.model_dump() for t in calls]}

    @app.get('/api/health')
    def health():
        return {'status': 'ok', 'mode': 'demo' if settings.demo else 'live',
                'model': settings.model if not settings.demo else None, 'max_tools': 6, 'max_depth': 2}

    @app.post('/api/users', status_code=201)
    def login(data: LoginInput):
        with Session(engine) as s:
            user = User(nickname=data.nickname)
            s.add(user)
            s.commit()
            s.refresh(user)
            return {'id': user.id, 'nickname': user.nickname, 'token': user.token}

    @app.get('/api/me')
    def me(user: User = Depends(current_user)):
        return {'id': user.id, 'nickname': user.nickname}

    @app.get('/api/rooms')
    def rooms():
        with Session(engine) as s:
            return s.exec(select(Room).order_by(Room.created_at)).all()

    @app.post('/api/rooms', status_code=201)
    async def create_room(data: RoomInput, _: User = Depends(current_user)):
        with Session(engine) as s:
            room = Room(**data.model_dump())
            s.add(room)
            s.commit()
            s.refresh(room)
            result = room.model_dump()
        for room_id in list(hub.rooms):
            await hub.broadcast(room_id, {'type': 'rooms_changed'})
        return result

    @app.get('/api/bots')
    def bots():
        with Session(engine) as s:
            return s.exec(select(Bot).order_by(Bot.created_at)).all()

    @app.post('/api/bots', status_code=201)
    async def create_bot(data: BotInput, _: User = Depends(current_user)):
        with Session(engine) as s:
            bot = Bot(**data.model_dump())
            s.add(bot)
            try:
                s.commit()
            except IntegrityError:
                s.rollback()
                raise HTTPException(409, 'Bot 名称已存在') from None
            s.refresh(bot)
            result = bot.model_dump()
        for room_id in list(hub.rooms):
            await hub.broadcast(room_id, {'type': 'bots_changed'})
        return result

    @app.put('/api/rooms/{room_id}/bots')
    async def set_room_bots(room_id: str, data: RoomBotsInput, _: User = Depends(current_user)):
        ids = set(data.bot_ids)
        with Session(engine) as s:
            room_or_404(s, room_id)
            if any(s.get(Bot, bot_id) is None for bot_id in ids):
                raise HTTPException(404, 'Bot 不存在')
            for row in s.exec(select(RoomBot).where(RoomBot.room_id == room_id)).all():
                s.delete(row)
            s.flush()
            s.add_all([RoomBot(room_id=room_id, bot_id=bot_id) for bot_id in ids])
            s.commit()
        await hub.broadcast(room_id, {'type': 'bots_changed'})
        return {'bot_ids': sorted(ids)}

    @app.get('/api/rooms/{room_id}/state')
    def state(room_id: str):
        return snapshot(room_id)

    @app.get('/api/rooms/{room_id}/messages')
    def messages(room_id: str, before_id: str | None = None, limit: int = Query(100, ge=1, le=100)):
        with Session(engine) as s:
            room_or_404(s, room_id)
            return recent_messages(s, room_id, before_id, limit)

    @app.get('/api/rooms/{room_id}/tasks')
    def tasks(room_id: str):
        data = snapshot(room_id)
        return {'tasks': data['tasks'], 'tool_calls': data['tool_calls']}

    @app.get('/api/tasks/{task_id}')
    def task_detail(task_id: str):
        with Session(engine) as s:
            task = s.get(Task, task_id)
            if task is None:
                raise HTTPException(404, '任务不存在')
            tasks = s.exec(select(Task).where(Task.root_id == task.root_id).order_by(Task.created_at)).all()
            calls = s.exec(select(ToolCall).where(ToolCall.root_id == task.root_id).order_by(ToolCall.created_at)).all()
            return {'root_id': task.root_id, 'room_id': task.room_id,
                    'tasks': [t.model_dump() for t in tasks], 'tool_calls': [c.model_dump() for c in calls]}

    @app.websocket('/ws/rooms/{room_id}')
    async def chat(ws: WebSocket, room_id: str, token: str = ''):
        user = user_by_token(token)
        with Session(engine) as s:
            exists = s.get(Room, room_id) is not None
        if not user or not exists:
            await ws.close(code=1008)
            return
        await hub.connect(room_id, ws, {'id': user.id, 'nickname': user.nickname})
        try:
            await hub.send(ws, {'type': 'snapshot', **snapshot(room_id)})
            while True:
                raw = await ws.receive_text()
                payload = None
                try:
                    if len(raw) > 12000:
                        raise ValueError('消息过长')
                    payload = json.loads(raw)
                    if not isinstance(payload, dict):
                        raise ValueError('无效消息格式')
                    if payload.get('type') == 'ping':
                        await hub.send(ws, {'type': 'pong'})
                        continue
                    if payload.get('type') != 'message':
                        raise ValueError('不支持的事件类型')
                    data = ChatInput.model_validate(payload)
                    peers = runner.peers(room_id)
                    mentioned = [b for b in peers if re.search('@' + re.escape(b['name']) + r'(?![\w\-])', data.content)]
                    if len(mentioned) > 4:
                        raise ValueError('单条消息最多提及 4 个 Bot')
                    if mentioned and len(runner.jobs) + len(mentioned) > 16:
                        raise ValueError('Bot 任务繁忙，请稍后重试')
                    with Session(engine) as s:
                        old = s.exec(select(Message).where(Message.client_id == data.client_id)).first()
                        if old:
                            if old.sender_id != user.id or old.room_id != room_id:
                                raise ValueError('消息 ID 冲突，请重新发送')
                            await hub.send(ws, {'type': 'message', 'message': old.model_dump()})
                            continue
                        message = Message(room_id=room_id, kind='user', sender_id=user.id,
                                          sender_name=user.nickname, content=data.content, client_id=data.client_id)
                        s.add(message)
                        s.commit()
                        s.refresh(message)
                        result = message.model_dump()
                    await hub.broadcast(room_id, {'type': 'message', 'message': result})
                    for bot in mentioned:
                        await runner.schedule(room_id, bot, data.content, message.id)
                except (ValueError, ValidationError) as exc:
                    await hub.send(ws, {'type': 'error', 'message': str(exc)[:500],
                                        'client_id': payload.get('client_id') if isinstance(payload, dict) else None})
        except WebSocketDisconnect:
            pass
        except (RuntimeError, OSError, TimeoutError):
            pass
        finally:
            await hub.disconnect(room_id, ws)

    return app


app = create_app()
