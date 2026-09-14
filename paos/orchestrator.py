"""
Agent orchestration engine for PAOS Live Operations
Handles workflow execution, task routing, and approval gates
"""

from sqlalchemy.orm import Session
from paos import models, schemas
from datetime import datetime
from typing import Dict, Any, Optional
import asyncio
import json


class AgentOrchestrator:
    """Orchestrates agent execution and task workflows"""
    
    def __init__(self):
        self.running_tasks = {}
    
    async def execute_task(self, db: Session, task: models.Task) -> models.Run:
        """Execute a task with its assigned agent"""
        # Create a new run
        run = models.Run(
            task_id=task.id,
            agent_name=task.assigned_agent,
            status=models.RunStatus.RUNNING.value,
            input_data=task.input_data,
            started_at=datetime.utcnow(),
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        
        # Update task status
        task.status = models.RunStatus.RUNNING.value
        task.started_at = datetime.utcnow()
        db.commit()
        
        # Create event
        self._create_event(
            db,
            task_id=task.id,
            run_id=run.id,
            event_type="agent_started",
            agent_name=task.assigned_agent,
            message=f"{task.assigned_agent} agent started",
        )
        
        # Store reference for async execution
        self.running_tasks[run.id] = {"task": task, "run": run}
        
        # Simulate agent execution (in real implementation, call actual agent)
        asyncio.create_task(self._run_agent_simulation(db, task, run))
        
        return run
    
    async def _run_agent_simulation(self, db: Session, task: models.Task, run: models.Run):
        """Simulate agent execution (placeholder for real LangGraph integration)"""
        try:
            # Simulate thinking/processing
            await asyncio.sleep(1)
            
            # Simulate tool usage
            tools_used = [
                {"tool": "search", "query": task.input_data.get("query", ""), "result_count": 42}
            ]
            
            # Check if approval is needed
            if self._needs_approval(task):
                run.status = models.RunStatus.AWAITING_APPROVAL.value
                task.status = models.RunStatus.AWAITING_APPROVAL.value
                
                # Create approval request
                approval = models.Approval(
                    task_id=task.id,
                    approval_level=models.ApprovalLevel.COMMUNICATE.value,
                    action_type="send_email",
                    required_reason="Task requires approval before proceeding",
                    status="pending",
                )
                db.add(approval)
                db.commit()
                
                self._create_event(
                    db,
                    task_id=task.id,
                    run_id=run.id,
                    event_type="approval_required",
                    message="Awaiting approval to continue",
                    data={"approval_id": approval.id},
                )
            else:
                # Complete the run
                run.status = models.RunStatus.COMPLETED.value
                run.output_data = {"result": "success", "items": 42}
                run.tools_used = tools_used
                run.completed_at = datetime.utcnow()
                
                task.status = models.RunStatus.COMPLETED.value
                task.output_data = run.output_data
                task.completed_at = datetime.utcnow()
                
                self._create_event(
                    db,
                    task_id=task.id,
                    run_id=run.id,
                    event_type="completed",
                    message="Task completed successfully",
                )
            
            db.commit()
            
        except Exception as e:
            run.status = models.RunStatus.FAILED.value
            run.error_message = str(e)
            task.status = models.RunStatus.FAILED.value
            task.error_message = str(e)
            db.commit()
            
            self._create_event(
                db,
                task_id=task.id,
                run_id=run.id,
                event_type="error",
                message=f"Task failed: {str(e)}",
            )
    
    async def resume_task(self, db: Session, task: models.Task):
        """Resume a task after approval"""
        task.status = models.RunStatus.RUNNING.value
        db.commit()
        
        # Get the current run
        run = db.query(models.Run).filter(models.Run.task_id == task.id).order_by(
            models.Run.created_at.desc()
        ).first()
        
        if run:
            self._create_event(
                db,
                task_id=task.id,
                run_id=run.id,
                event_type="resumed",
                message="Task resumed after approval",
            )
    
    async def verify_connection(self, db: Session, connection: models.Connection):
        """Verify a connection to an external service"""
        # Placeholder for real verification logic
        if connection.service_type == "openai":
            # Would test OpenAI API key here
            pass
        elif connection.service_type == "gmail":
            # Would test Gmail OAuth here
            pass
        else:
            raise ValueError(f"Unknown service type: {connection.service_type}")
    
    def _needs_approval(self, task: models.Task) -> bool:
        """Determine if task needs approval"""
        action_types = task.input_data.get("action_types", [])
        return any(at in ["communicate", "purchase", "financial"] for at in action_types)
    
    def _create_event(
        self,
        db: Session,
        event_type: str,
        message: str,
        task_id: Optional[str] = None,
        run_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ):
        """Create an event for real-time dashboard updates"""
        event = models.Event(
            event_type=event_type,
            message=message,
            task_id=task_id,
            run_id=run_id,
            agent_name=agent_name,
            data=data,
            timestamp=datetime.utcnow(),
        )
        db.add(event)
        db.commit()


# Singleton instance
agent_orchestrator = AgentOrchestrator()
