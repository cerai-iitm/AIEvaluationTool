import asyncio

from fastapi import WebSocket

class WSManager:
    def __init__(self):
        self.connections = []
        self._send_locks = {}
        self.disconnected_by_frontend = False  # 👈 add this

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)
        self._send_locks[websocket] = asyncio.Lock()
        self.disconnected_by_frontend = False

    def disconnect(self, websocket: WebSocket):
        if websocket in self.connections:
            self.connections.remove(websocket)
        self._send_locks.pop(websocket, None)

    async def send_one(self, websocket: WebSocket, message: dict):
        lock = self._send_locks.get(websocket)
        if lock is None:
            return

        async with lock:
            await websocket.send_json(message)

    async def send_all(self, message: dict):
        stale_connections = []
        for ws in list(self.connections):
            try:
                await self.send_one(ws, message)
            except Exception:
                stale_connections.append(ws)

        for ws in stale_connections:
            self.disconnect(ws)

    def is_empty(self) -> bool:
        return len(self.connections) == 0        

ws_manager = WSManager()            
