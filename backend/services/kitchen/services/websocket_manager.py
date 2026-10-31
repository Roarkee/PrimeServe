from fastapi import WebSocket
from collections import defaultdict
from typing import Any

class WebSocketManager:
    def __init__(self):
        self.connections : dict[tuple[str,str,str], set[WebSocket]] = defaultdict(set)
        self.connection_scopes: dict[WebSocket, tuple[str, str, str]] = {}