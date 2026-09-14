"""
Shared execution context for multi-agent coordination
"""

from typing import Any, Dict, Optional, Callable
import asyncio
from datetime import datetime
import json


class SharedContext:
    """Thread-safe shared context for agent coordination"""
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.lock = asyncio.Lock()
        self.history: list = []
        self.metadata: Dict[str, Any] = {
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from context"""
        async with self.lock:
            return self.data.get(key)
    
    async def set(self, key: str, value: Any, agent: Optional[str] = None):
        """Set value in context"""
        async with self.lock:
            self.data[key] = value
            self.history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "agent": agent,
                "action": "set",
                "key": key,
                "value_type": type(value).__name__
            })
            self.metadata["updated_at"] = datetime.utcnow().isoformat()
    
    async def update(self, key: str, fn: Callable, agent: Optional[str] = None):
        """Update value using function"""
        async with self.lock:
            current = self.data.get(key)
            updated = fn(current)
            self.data[key] = updated
            self.history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "agent": agent,
                "action": "update",
                "key": key,
                "value_type": type(updated).__name__
            })
            self.metadata["updated_at"] = datetime.utcnow().isoformat()
    
    async def append(self, key: str, value: Any, agent: Optional[str] = None):
        """Append to list in context"""
        async with self.lock:
            if key not in self.data:
                self.data[key] = []
            self.data[key].append(value)
            self.history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "agent": agent,
                "action": "append",
                "key": key,
                "value_type": type(value).__name__
            })
            self.metadata["updated_at"] = datetime.utcnow().isoformat()
    
    async def get_all(self) -> Dict[str, Any]:
        """Get all data"""
        async with self.lock:
            return self.data.copy()
    
    async def clear_key(self, key: str, agent: Optional[str] = None):
        """Clear a key"""
        async with self.lock:
            if key in self.data:
                del self.data[key]
                self.history.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent": agent,
                    "action": "delete",
                    "key": key,
                })
    
    def get_history(self) -> list:
        """Get change history"""
        return self.history.copy()
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get context metadata"""
        return self.metadata.copy()
    
    async def export(self) -> Dict[str, Any]:
        """Export entire context as JSON"""
        async with self.lock:
            return {
                "data": self.data.copy(),
                "metadata": self.metadata.copy(),
                "history_length": len(self.history)
            }
