"""
Pydantic schemas for API requests/responses
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class RunStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"


class ApprovalLevelEnum(str, Enum):
    NONE = "none"
    READ = "read"
    ANALYZE = "analyze"
    CREATE = "create"
    COMMUNICATE = "communicate"
    PURCHASE = "purchase"
    FINANCIAL = "financial"
    IRREVERSIBLE = "irreversible"


class ConnectionStatusEnum(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    ACTION_REQUIRED = "action_required"


# Task Schemas
class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    assigned_agent: str
    input_data: Dict[str, Any]


class TaskUpdate(BaseModel):
    status: Optional[RunStatusEnum] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: str
    assigned_agent: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    estimated_cost: int
    actual_cost: int
    
    class Config:
        from_attributes = True


# Run Schemas
class RunCreate(BaseModel):
    task_id: str
    agent_name: str
    input_data: Dict[str, Any]


class RunResponse(BaseModel):
    id: str
    task_id: str
    agent_name: str
    status: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    thinking_process: Optional[Dict[str, Any]]
    tools_used: Optional[List[Dict[str, Any]]]
    token_count_input: int
    token_count_output: int
    cost_cents: int
    duration_seconds: Optional[int]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True


# Approval Schemas
class ApprovalCreate(BaseModel):
    task_id: str
    approval_level: ApprovalLevelEnum
    action_type: str
    required_reason: Optional[str] = None


class ApprovalDecision(BaseModel):
    approved: bool
    decision_comment: Optional[str] = None


class ApprovalResponse(BaseModel):
    id: str
    task_id: str
    approval_level: str
    action_type: str
    status: str
    created_at: datetime
    decided_at: Optional[datetime]
    requested_by: Optional[str]
    approved_by: Optional[str]
    decision_comment: Optional[str]
    
    class Config:
        from_attributes = True


# Connection Schemas
class ConnectionCreate(BaseModel):
    name: str
    service_type: str
    credentials: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None


class ConnectionUpdate(BaseModel):
    credentials: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None


class ConnectionResponse(BaseModel):
    id: str
    name: str
    service_type: str
    status: str
    last_verified: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Event Schemas
class EventResponse(BaseModel):
    id: str
    task_id: Optional[str]
    run_id: Optional[str]
    event_type: str
    timestamp: datetime
    agent_name: Optional[str]
    message: Optional[str]
    data: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


# Dashboard Live Operations
class AgentOperation(BaseModel):
    """Real-time agent operation for dashboard"""
    agent_name: str
    status: str
    task_id: str
    run_id: Optional[str]
    progress_message: str
    timestamp: datetime


class OperationsUpdate(BaseModel):
    """WebSocket message for live dashboard updates"""
    event_type: str  # "status_update", "agent_started", "approval_required", "completed"
    timestamp: datetime
    task_id: str
    data: Dict[str, Any]
