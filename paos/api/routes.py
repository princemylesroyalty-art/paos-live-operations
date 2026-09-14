"""
Core API routes for PAOS Live Operations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from paos.database import get_db
from paos import models, schemas
from paos.connections import connection_manager
from paos.orchestrator import agent_orchestrator
from typing import List

router = APIRouter(prefix="/api", tags=["operations"])


# Task endpoints
@router.post("/tasks", response_model=schemas.TaskResponse)
async def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    """Create a new task"""
    db_task = models.Task(
        name=task.name,
        description=task.description,
        assigned_agent=task.assigned_agent,
        input_data=task.input_data,
        status=models.RunStatus.PENDING.value,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.get("/tasks/{task_id}", response_model=schemas.TaskResponse)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get task by ID"""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/tasks", response_model=List[schemas.TaskResponse])
async def list_tasks(db: Session = Depends(get_db)):
    """List all tasks"""
    return db.query(models.Task).order_by(models.Task.created_at.desc()).all()


@router.post("/tasks/{task_id}/run")
async def run_task(task_id: str, db: Session = Depends(get_db)):
    """Execute a task with its assigned agent"""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Trigger agent orchestration
    run = await agent_orchestrator.execute_task(db, task)
    return {"run_id": run.id, "status": run.status}


# Run endpoints
@router.get("/runs/{run_id}", response_model=schemas.RunResponse)
async def get_run(run_id: str, db: Session = Depends(get_db)):
    """Get run by ID"""
    run = db.query(models.Run).filter(models.Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/tasks/{task_id}/runs", response_model=List[schemas.RunResponse])
async def get_task_runs(task_id: str, db: Session = Depends(get_db)):
    """Get all runs for a task"""
    return db.query(models.Run).filter(models.Run.task_id == task_id).all()


# Approval endpoints
@router.post("/approvals", response_model=schemas.ApprovalResponse)
async def create_approval(approval: schemas.ApprovalCreate, db: Session = Depends(get_db)):
    """Create an approval request"""
    db_approval = models.Approval(
        task_id=approval.task_id,
        approval_level=approval.approval_level.value,
        action_type=approval.action_type,
        required_reason=approval.required_reason,
        status="pending",
    )
    db.add(db_approval)
    db.commit()
    db.refresh(db_approval)
    return db_approval


@router.get("/approvals/{approval_id}", response_model=schemas.ApprovalResponse)
async def get_approval(approval_id: str, db: Session = Depends(get_db)):
    """Get approval by ID"""
    approval = db.query(models.Approval).filter(models.Approval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


@router.post("/approvals/{approval_id}/decide")
async def decide_approval(
    approval_id: str,
    decision: schemas.ApprovalDecision,
    db: Session = Depends(get_db)
):
    """Approve or reject an approval request"""
    approval = db.query(models.Approval).filter(models.Approval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    approval.status = "approved" if decision.approved else "rejected"
    approval.decision_comment = decision.decision_comment
    from datetime import datetime
    approval.decided_at = datetime.utcnow()
    approval.approved_by = "user"  # TODO: Get from auth context
    
    db.commit()
    db.refresh(approval)
    
    # Resume task if approved
    if decision.approved:
        task = approval.task
        if task.status == models.RunStatus.AWAITING_APPROVAL.value:
            await agent_orchestrator.resume_task(db, task)
    
    return approval


# Connection endpoints
@router.post("/connections", response_model=schemas.ConnectionResponse)
async def create_connection(
    connection: schemas.ConnectionCreate,
    db: Session = Depends(get_db)
):
    """Create a new connection"""
    db_connection = connection_manager.create_connection(
        db,
        connection.name,
        connection.service_type,
        connection.credentials,
        connection.config
    )
    return db_connection


@router.get("/connections", response_model=List[schemas.ConnectionResponse])
async def list_connections(db: Session = Depends(get_db)):
    """List all connections"""
    return connection_manager.list_connections(db)


@router.get("/connections/{connection_id}", response_model=schemas.ConnectionResponse)
async def get_connection(connection_id: str, db: Session = Depends(get_db)):
    """Get connection by ID"""
    connection = connection_manager.get_connection(db, connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    return connection


@router.post("/connections/{connection_id}/verify")
async def verify_connection(connection_id: str, db: Session = Depends(get_db)):
    """Verify a connection (test credentials)"""
    connection = connection_manager.get_connection(db, connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    # Verify based on service type
    try:
        await agent_orchestrator.verify_connection(db, connection)
        connection_manager.update_connection_status(
            db, connection_id, models.ConnectionStatus.CONNECTED.value
        )
        return {"status": "connected", "message": "Connection verified successfully"}
    except Exception as e:
        connection_manager.update_connection_status(
            db, connection_id, models.ConnectionStatus.ACTION_REQUIRED.value, str(e)
        )
        return {"status": "error", "message": str(e)}


# Event/Activity endpoints
@router.get("/events", response_model=List[schemas.EventResponse])
async def list_events(
    task_id: str = None,
    run_id: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get events (activity log)"""
    query = db.query(models.Event)
    
    if task_id:
        query = query.filter(models.Event.task_id == task_id)
    if run_id:
        query = query.filter(models.Event.run_id == run_id)
    
    return query.order_by(models.Event.timestamp.desc()).limit(limit).all()
