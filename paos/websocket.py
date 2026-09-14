"""
WebSocket support for real-time dashboard updates
"""

from fastapi import WebSocket, APIRouter, Depends
from sqlalchemy.orm import Session
from paos.database import get_db
from paos import models
from datetime import datetime, timedelta
import json
import asyncio

ws_router = APIRouter()
active_connections = []


class ConnectionManager:
    """Manages WebSocket connections for broadcasting updates"""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass
    
    async def broadcast_event(self, event: models.Event):
        """Convert event to OperationsUpdate and broadcast"""
        message = {
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "task_id": event.task_id,
            "message": event.message,
            "data": event.data or {},
        }
        await self.broadcast(message)


manager = ConnectionManager()


@ws_router.websocket("/ws/operations")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """WebSocket endpoint for live operations updates"""
    await manager.connect(websocket)
    try:
        # Send initial state
        tasks = db.query(models.Task).order_by(models.Task.created_at.desc()).limit(10).all()
        initial_state = {
            "type": "initial_state",
            "tasks": [
                {
                    "id": t.id,
                    "name": t.name,
                    "status": t.status,
                    "agent": t.assigned_agent,
                }
                for t in tasks
            ],
        }
        await websocket.send_json(initial_state)
        
        # Stream recent events
        last_event_time = datetime.utcnow() - timedelta(minutes=5)
        while True:
            # Get new events since last check
            events = db.query(models.Event).filter(
                models.Event.timestamp > last_event_time
            ).order_by(models.Event.timestamp.asc()).all()
            
            for event in events:
                await manager.broadcast_event(event)
                last_event_time = event.timestamp
            
            await asyncio.sleep(1)  # Poll every second
    
    except Exception:
        pass
    finally:
        manager.disconnect(websocket)
