import asyncio
import json
import logging

from fastapi import WebSocket

from services.redis_client import redis_async_client

# NOTE: this module is imported very early in main.py (before the
# sys.path.insert that makes the top-level `lib` package importable), so
# it must not depend on `lib.utils.get_logger` like most other services do
# — stdlib logging only.
logger = logging.getLogger(__name__)

# All app-backend replicas publish/subscribe on this one channel so a
# progress event sent by whichever replica is actually running a
# background task (test run or analysis) reaches WebSocket clients
# connected to ANY replica, not just that one.
WS_BROADCAST_CHANNEL = "ws_broadcast"


class WSManager:
    def __init__(self):
        self.connections = []
        self._send_locks = {}
        self.disconnected_by_frontend = False  # 👈 add this
        self._pubsub_task = None

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

    async def _deliver_local(self, message: dict):
        """Deliver to WebSocket clients connected to this process only."""
        stale_connections = []
        for ws in list(self.connections):
            try:
                await self.send_one(ws, message)
            except Exception:
                stale_connections.append(ws)

        for ws in stale_connections:
            self.disconnect(ws)

    async def send_all(self, message: dict):
        """
        Broadcast to every WebSocket client across every app-backend
        replica, not just this process's local connections. Publishes to
        Redis; every replica's subscriber loop (including this one)
        receives it and delivers to its own local clients. This matters
        because a test-run/analysis background task can be running on a
        different replica than the one a given browser's WebSocket landed
        on (nginx pins to whichever replica IP it resolved at startup).

        Falls back to local-only delivery if Redis is unreachable, so a
        single-replica/no-Redis setup still works.
        """
        try:
            await redis_async_client.publish(WS_BROADCAST_CHANNEL, json.dumps(message))
        except Exception as e:
            logger.warning(f"Redis publish failed, falling back to local-only WS delivery: {e}")
            await self._deliver_local(message)

    def is_empty(self) -> bool:
        return len(self.connections) == 0

    async def start_pubsub_listener(self):
        """
        Call once at app startup (per process). Subscribes to the shared
        broadcast channel and fans incoming messages out to this process's
        local WebSocket connections.
        """
        if self._pubsub_task is not None:
            return
        self._pubsub_task = asyncio.create_task(self._listen())

    async def _listen(self):
        while True:
            try:
                pubsub = redis_async_client.pubsub()
                await pubsub.subscribe(WS_BROADCAST_CHANNEL)
                async for message in pubsub.listen():
                    if message.get("type") != "message":
                        continue
                    try:
                        payload = json.loads(message["data"])
                    except (TypeError, ValueError):
                        continue
                    await self._deliver_local(payload)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.warning(f"WS pubsub listener error, retrying in 3s: {e}")
                await asyncio.sleep(3)


ws_manager = WSManager()
