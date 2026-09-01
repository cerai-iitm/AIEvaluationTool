import asyncio

from fastapi import WebSocket

class WSManager:
    def __init__(self):
        self.connections = []
        self._send_locks = {}
        self.disconnected_by_frontend = False  # 👈 add this
        self.subscriptions: dict[WebSocket, set[str]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)
        self._send_locks[websocket] = asyncio.Lock()
        self.subscriptions[websocket] = set()
        self.disconnected_by_frontend = False

    def disconnect(self, websocket: WebSocket) -> set[str]:
        """Removes the socket and returns the set of keys it was subscribed to."""
        if websocket in self.connections:
            self.connections.remove(websocket)
        self._send_locks.pop(websocket, None)
        return self.subscriptions.pop(websocket, set())

    def subscribe(self, websocket: WebSocket, key: str):
        if key is None:
            return
        self.subscriptions.setdefault(websocket, set()).add(str(key))

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

    async def send_to_run(self, key, message: dict):
        """Sends only to sockets subscribed to this key (e.g. runId/runName)."""
        key = str(key)
        stale_connections = []
        for ws in list(self.connections):
            if key not in self.subscriptions.get(ws, set()):
                continue
            try:
                await self.send_one(ws, message)
            except Exception:
                stale_connections.append(ws)

        for ws in stale_connections:
            self.disconnect(ws)

    def is_empty(self) -> bool:
        return len(self.connections) == 0

ws_manager = WSManager()
