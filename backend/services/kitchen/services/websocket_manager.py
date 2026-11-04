from fastapi import WebSocket
from collections import defaultdict
from typing import Any
class WebSocketManager:
    def __init__(self):
        self.connections: dict[tuple[str, str | None, str],set[WebSocket]] = defaultdict(set)

        self.connection_scopes: dict[WebSocket,tuple[str, str | None, str]] = {}

    async def connect(self, websocket: WebSocket, restaurant_id:str, station_id:str, branch_id:str|None)->None:
        scope = (restaurant_id, station_id, branch_id)
        self.connections[scope].add(websocket)
        self.connection_scopes[websocket] = scope


    async def disconnect(self, websocket):
        scope = self.connection_scopes.pop(websocket, None)
        if scope is None:
            return

        self.connections[scope].discard(websocket)

        if not self.connections[scope]:
            del self.connections[scope]

    async def broadcast_to_station(self,restaurant_id: str,branch_id: str | None,
                                   station_id: str,
                                   message: dict[str, Any],) -> int:
        scope = (restaurant_id, branch_id, station_id)
        clients = list(self.connections.get(scope, set()))

        disconnected = []

        for websocket in clients:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(websocket)

        return len(clients) - len(disconnected)


websocket_manager = WebSocketManager()


