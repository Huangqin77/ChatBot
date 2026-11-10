import asyncio
from collections import defaultdict

from fastapi import WebSocket


class Hub:
    def __init__(self):
        self.rooms: dict[str, dict[WebSocket, dict]] = defaultdict(dict)
        self.locks: dict[WebSocket, asyncio.Lock] = {}

    async def send(self, ws: WebSocket, event: dict):
        lock = self.locks.get(ws)
        if lock is None:
            return
        async with lock:
            await asyncio.wait_for(ws.send_json(event), timeout=3)

    async def broadcast(self, room_id: str, event: dict):
        peers = list(self.rooms.get(room_id, {}))
        results = await asyncio.gather(*(self.send(ws, event) for ws in peers), return_exceptions=True)
        for ws, result in zip(peers, results):
            if isinstance(result, BaseException):
                self.rooms[room_id].pop(ws, None)
                self.locks.pop(ws, None)

    async def connect(self, room_id, ws, user):
        await ws.accept()
        self.rooms[room_id][ws] = user
        self.locks[ws] = asyncio.Lock()
        await self.presence(room_id)

    async def disconnect(self, room_id, ws):
        self.rooms[room_id].pop(ws, None)
        self.locks.pop(ws, None)
        await self.presence(room_id)
        if not self.rooms[room_id]:
            self.rooms.pop(room_id, None)

    async def presence(self, room_id):
        unique = {u['id']: u for u in self.rooms.get(room_id, {}).values()}
        await self.broadcast(room_id, {'type': 'presence', 'users': list(unique.values())})
