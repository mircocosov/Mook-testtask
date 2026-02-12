import json
from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class RealtimeHub:
    def __init__(self) -> None:
        self.connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, wishlist_public_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections[wishlist_public_id].add(websocket)

    def disconnect(self, wishlist_public_id: str, websocket: WebSocket) -> None:
        self.connections[wishlist_public_id].discard(websocket)

    async def broadcast(self, wishlist_public_id: str, event_type: str, payload: dict[str, Any]) -> None:
        message = json.dumps({"type": event_type, "version": 1, "payload": payload})
        stale: list[WebSocket] = []
        for ws in self.connections[wishlist_public_id]:
            try:
                await ws.send_text(message)
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect(wishlist_public_id, ws)


hub = RealtimeHub()
