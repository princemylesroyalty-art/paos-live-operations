"""
Inter-agent message broker for coordination
"""

from typing import Any, Dict, Callable, List, Optional
import asyncio
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    """Types of messages between agents"""
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    ERROR = "error"
    STATUS = "status"


class Message:
    """Message between agents"""
    
    def __init__(
        self,
        from_agent: str,
        to_agent: str,
        msg_type: MessageType,
        content: Dict[str, Any],
        msg_id: Optional[str] = None
    ):
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.msg_type = msg_type
        self.content = content
        self.msg_id = msg_id or f"{from_agent}-{to_agent}-{id(self)}"
        self.timestamp = datetime.utcnow()
        self.replied = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.msg_id,
            "from": self.from_agent,
            "to": self.to_agent,
            "type": self.msg_type.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "replied": self.replied
        }


class MessageBroker:
    """Central message broker for agent communication"""
    
    def __init__(self):
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.subscribers: Dict[str, List[Callable]] = {}  # topic -> handlers
        self.message_history: List[Message] = []
        self.max_history = 10000
    
    async def publish(self, message: Message) -> bool:
        """Publish message to topic"""
        await self.message_queue.put(message)
        self.message_history.append(message)
        
        # Trim history
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history:]
        
        # Notify subscribers
        topic = f"{message.from_agent}:{message.to_agent}"
        if topic in self.subscribers:
            for handler in self.subscribers[topic]:
                await handler(message)
        
        return True
    
    async def subscribe(self, from_agent: str, to_agent: str, handler: Callable) -> str:
        """Subscribe to messages"""
        topic = f"{from_agent}:{to_agent}"
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(handler)
        return topic
    
    async def unsubscribe(self, topic: str, handler: Callable):
        """Unsubscribe from messages"""
        if topic in self.subscribers:
            self.subscribers[topic].remove(handler)
    
    async def get_message(self, timeout: Optional[float] = None) -> Optional[Message]:
        """Get next message"""
        try:
            message = await asyncio.wait_for(
                self.message_queue.get(),
                timeout=timeout
            )
            return message
        except asyncio.TimeoutError:
            return None
    
    def get_history(
        self,
        from_agent: Optional[str] = None,
        to_agent: Optional[str] = None,
        limit: int = 100
    ) -> List[Message]:
        """Get message history with optional filtering"""
        history = self.message_history
        
        if from_agent:
            history = [m for m in history if m.from_agent == from_agent]
        
        if to_agent:
            history = [m for m in history if m.to_agent == to_agent]
        
        return history[-limit:]
    
    def get_message_stats(self) -> Dict[str, Any]:
        """Get message statistics"""
        by_type = {}
        by_agent = {}
        
        for msg in self.message_history:
            msg_type = msg.msg_type.value
            by_type[msg_type] = by_type.get(msg_type, 0) + 1
            
            agent = msg.from_agent
            by_agent[agent] = by_agent.get(agent, 0) + 1
        
        return {
            "total_messages": len(self.message_history),
            "by_type": by_type,
            "by_agent": by_agent,
            "queue_size": self.message_queue.qsize()
        }
