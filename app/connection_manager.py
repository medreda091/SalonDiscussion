"""Gestionnaire des connexions WebSocket, salon par salon."""

from fastapi import WebSocket


class ConnectionManager:
    """Garde la liste des clients connectés pour chaque salon."""

    def __init__(self):
        # Dictionnaire : nom du salon -> liste des WebSockets connectés.
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_name: str):
        """Accepte la connexion et l'ajoute au salon demandé."""
        await websocket.accept()
        self.active_connections.setdefault(room_name, []).append(websocket)

    def disconnect(self, websocket: WebSocket, room_name: str):
        """Retire un client déconnecté de son salon."""
        connections = self.active_connections.get(room_name, [])
        if websocket in connections:
            connections.remove(websocket)

    async def broadcast(self, message: dict, room_name: str):
        """Envoie un message à tous les clients du salon."""
        for connection in list(self.active_connections.get(room_name, [])):
            try:
                await connection.send_json(message)
            except Exception:
                # Un client parti sans prévenir ne doit pas casser la diffusion.
                self.disconnect(connection, room_name)


manager = ConnectionManager()
