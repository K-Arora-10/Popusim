from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
from typing import Dict, List

logger = logging.getLogger("popusim.ws")
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # Maps simulation_id -> list of active WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, simulation_id: str):
        await websocket.accept()
        if simulation_id not in self.active_connections:
            self.active_connections[simulation_id] = []
        self.active_connections[simulation_id].append(websocket)
        logger.info(f"WebSocket client connected to simulation {simulation_id}")

    def disconnect(self, websocket: WebSocket, simulation_id: str):
        if simulation_id in self.active_connections:
            if websocket in self.active_connections[simulation_id]:
                self.active_connections[simulation_id].remove(websocket)
            if not self.active_connections[simulation_id]:
                del self.active_connections[simulation_id]
        logger.info(f"WebSocket client disconnected from simulation {simulation_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict, simulation_id: str):
        if simulation_id in self.active_connections:
            connections = list(self.active_connections[simulation_id])
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Error broadcasting to WS: {e}")
                    # Auto clean dead connection
                    self.disconnect(connection, simulation_id)

manager = ConnectionManager()

@router.websocket("/ws/simulation/{simulation_id}")
async def websocket_endpoint(websocket: WebSocket, simulation_id: str):
    await manager.connect(websocket, simulation_id)
    try:
        while True:
            # Keep connection open, listen for client pings if needed
            data = await websocket.receive_text()
            # If client sends a ping, reply pong
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, simulation_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, simulation_id)
