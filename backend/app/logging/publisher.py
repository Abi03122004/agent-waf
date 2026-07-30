import json
from typing import List
from fastapi import WebSocket

class EventPublisher:
    def __init__(self) -> None:
        self._connections: List[WebSocket] = []

    async def register(self, websocket: WebSocket) -> None:
        """Register a new active WebSocket connection."""
        await websocket.accept()
        self._connections.append(websocket)

    def unregister(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if websocket in self._connections:
            self._connections.remove(websocket)

    async def publish(self, event_data: dict) -> None:
        """Broadcast serialized event payload to all connected clients."""
        disconnected = []
        for connection in self._connections:
            try:
                await connection.send_json(event_data)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.unregister(conn)

# Create singleton global event publisher instance
event_publisher = EventPublisher()
