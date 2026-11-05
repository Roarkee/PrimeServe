import logging
from collections import defaultdict
from typing import Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    In-memory connection manager for Kitchen Display System (KDS) WebSockets.

    LIMITATION:
    This connection manager maintains active WebSockets in memory on the current process.
    If the Kitchen service is scaled horizontally across multiple processes or instances,
    a pub/sub broker (e.g. Redis Pub/Sub) would be required so that broadcasts reach
    clients connected to other workers. For the current single-service deployment,
    in-memory scoping is used.

    Scope: (restaurant_id, station_id)
    """

    def __init__(self):
        # Key: (restaurant_id, station_id) -> set of active WebSockets
        self.connections: dict[tuple[str, str], set[WebSocket]] = defaultdict(set)
        # Reverse mapping: WebSocket -> (restaurant_id, station_id)
        self.connection_scopes: dict[WebSocket, tuple[str, str]] = {}

    def connect(self, websocket: WebSocket, restaurant_id: str, station_id: str) -> None:
        """Register a connected and authenticated WebSocket."""
        scope = (str(restaurant_id), str(station_id))
        self.connections[scope].add(websocket)
        self.connection_scopes[websocket] = scope
        logger.debug("Registered KDS connection for scope %s (total: %d)", scope, len(self.connections[scope]))

    def disconnect(self, websocket: WebSocket) -> None:
        """Unregister and clean up a WebSocket connection."""
        scope = self.connection_scopes.pop(websocket, None)
        if scope is None:
            return

        station_set = self.connections.get(scope)
        if station_set is not None:
            station_set.discard(websocket)
            if not station_set:
                self.connections.pop(scope, None)
        logger.debug("Unregistered KDS connection for scope %s", scope)

    async def broadcast_to_station(
        self,
        restaurant_id: str,
        station_id: str,
        message: dict[str, Any],
    ) -> int:
        """
        Broadcast a JSON message to all KDS clients connected to a station.
        Stale/broken connections are cleaned up automatically.
        Returns the number of clients that successfully received the message.
        """
        scope = (str(restaurant_id), str(station_id))
        clients = list(self.connections.get(scope, set()))
        if not clients:
            return 0

        failed_clients: list[WebSocket] = []
        success_count = 0

        for ws in clients:
            try:
                await ws.send_json(message)
                success_count += 1
            except Exception as exc:
                logger.warning("Failed sending message to KDS client in scope %s: %s", scope, exc)
                failed_clients.append(ws)

        for ws in failed_clients:
            self.disconnect(ws)

        return success_count

    def get_connection_count(self, restaurant_id: str, station_id: str) -> int:
        """Get the count of active connections for a station scope."""
        scope = (str(restaurant_id), str(station_id))
        return len(self.connections.get(scope, set()))


websocket_manager = WebSocketManager()
