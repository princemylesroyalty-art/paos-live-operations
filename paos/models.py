"""
Database models for PAOS Live Operations
"""

from sqlalchemy import Column, String, DateTime, JSON, Integer, Boolean, ForeignKey, Enum, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

Base = declarative_base()


class RunStatus(str, enum.Enum):
    """Status of a task/run"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"


class ApprovalLevel(str, enum.Enum):
    """Approval levels for actions"""
    NONE = "none"
    READ = "read"
    ANALYZE = "analyze"
    CREATE = "create"
    COMMUNICATE = "communicate"
    PURCHASE = "purchase"
    FINANCIAL = "financial"
    IRREVERSIBLE = "irreversible"


class ConnectionStatus(str, enum.Enum):
    """Status of external connections"""
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    ACTION_REQUIRED = "action_required"


class Task(Base):
    """Top-level task or operation"""
    __tablename__ = "tasks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default=RunStatus.PENDING.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Execution details
    assigned_agent = Column(String(255))
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)
    
    # Cost tracking
    estimated_cost = Column(Integer, default=0)  # in cents
    actual_cost = Column(Integer, default=0)
    
    # Relations
    runs = relationship("Run", back_populates="task", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="task", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="task", cascade="all, delete-orphan")


class Run(Base):
    """Individual run/execution of an agent"""
    __tablename__ = "runs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)
    agent_name = Column(String(255), nullable=False)
    status = Column(String(50), default=RunStatus.PENDING.value)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Execution data
    input_data = Column(JSON)
    output_data = Column(JSON)
    thinking_process = Column(JSON)  # LangGraph thought trace
    tools_used = Column(JSON)  # Array of tool calls
    
    # Metrics
    token_count_input = Column(Integer, default=0)
    token_count_output = Column(Integer, default=0)
    cost_cents = Column(Integer, default=0)
    duration_seconds = Column(Integer)
    
    error_message = Column(Text)
    
    task = relationship("Task", back_populates="runs")
    events = relationship("Event", back_populates="run", cascade="all, delete-orphan")


class Approval(Base):
    """Approval request for sensitive actions"""
    __tablename__ = "approvals"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)
    
    approval_level = Column(String(50), nullable=False)
    action_type = Column(String(255))  # e.g., "send_email", "charge_card", "post_content"
    required_reason = Column(Text)
    
    status = Column(String(50), default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    decided_at = Column(DateTime)
    
    requested_by = Column(String(255))
    approved_by = Column(String(255))
    decision_comment = Column(Text)
    
    task = relationship("Task", back_populates="approvals")


class Connection(Base):
    """External service connection with encrypted credentials"""
    __tablename__ = "connections"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    service_type = Column(String(100), nullable=False)  # openai, gmail, stripe, etc.
    status = Column(String(50), default=ConnectionStatus.DISCONNECTED.value)
    
    # Encrypted credentials stored as JSON
    credentials_encrypted = Column(Text)
    
    # Last verification
    last_verified = Column(DateTime)
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Metadata
    config = Column(JSON)  # Service-specific config


class Event(Base):
    """Real-time event log for streaming to dashboard"""
    __tablename__ = "events"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("tasks.id"))
    run_id = Column(String(36), ForeignKey("runs.id"))
    
    event_type = Column(String(100), nullable=False)  # started, tool_called, approved, completed, error
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    agent_name = Column(String(255))
    message = Column(Text)
    data = Column(JSON)
    
    task = relationship("Task", back_populates="events")
    run = relationship("Run", back_populates="events")
