"""
Central coordinator for multi-agent orchestration
"""

from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime
from paos.coordination.context_manager import SharedContext
from paos.coordination.message_broker import MessageBroker, Message, MessageType
from paos.agents import (
    CEOAgent, ResearchAgent, OpportunityAgent, SalesAgent,
    LeadAgent, RiskAgent, AutomationAgent
)
from sqlalchemy.orm import Session
from paos import models


class AgentCoordinator:
    """Coordinates multi-agent execution and communication"""
    
    def __init__(self):
        self.context = SharedContext()
        self.broker = MessageBroker()
        self.agents = {
            "ceo": CEOAgent(),
            "research": ResearchAgent(),
            "opportunity": OpportunityAgent(),
            "sales": SalesAgent(),
            "lead": LeadAgent(),
            "risk": RiskAgent(),
            "automation": AutomationAgent(),
        }
        self.active_runs: Dict[str, Dict[str, Any]] = {}
    
    async def coordinate(self, db: Session, task: models.Task, task_id: str) -> Dict[str, Any]:
        """Orchestrate multi-agent workflow"""
        run_id = f"run-{id(self)}"
        self.active_runs[run_id] = {
            "task_id": task_id,
            "status": "running",
            "started_at": datetime.utcnow(),
            "agents_executed": []
        }
        
        try:
            # Initialize context
            await self.context.set("task_id", task_id)
            await self.context.set("task_input", task.input_data)
            await self.context.set("approvals_pending", [])
            
            # Execute CEO agent (router)
            ceo_result = await self.agents["ceo"].execute(task.input_data)
            await self.context.set("ceo_output", ceo_result.output, "ceo")
            self.active_runs[run_id]["agents_executed"].append("ceo")
            
            # Execute research agent
            research_result = await self.agents["research"].execute({
                "query": task.input_data.get("query"),
                "market": task.input_data.get("market")
            })
            await self.context.set("research_output", research_result.output, "research")
            self.active_runs[run_id]["agents_executed"].append("research")
            
            # Execute opportunity agent
            opp_result = await self.agents["opportunity"].execute({
                "opportunities": research_result.output.get("opportunities", [])
            })
            await self.context.set("opportunity_output", opp_result.output, "opportunity")
            self.active_runs[run_id]["agents_executed"].append("opportunity")
            
            # Check if approval needed
            if opp_result.approval_required:
                approval = models.Approval(
                    task_id=task_id,
                    approval_level="communicate",
                    action_type="proceed_with_sales",
                    required_reason=opp_result.approval_reason,
                    status="pending"
                )
                db.add(approval)
                db.commit()
                
                await self.context.append("approvals_pending", approval.id)
                self.active_runs[run_id]["status"] = "awaiting_approval"
                
                return {
                    "run_id": run_id,
                    "status": "awaiting_approval",
                    "approval_id": approval.id,
                    "context": await self.context.export()
                }
            
            # Execute sales agent
            sales_result = await self.agents["sales"].execute({
                "opportunities": opp_result.output.get("top_opportunities", [])
            })
            await self.context.set("sales_output", sales_result.output, "sales")
            self.active_runs[run_id]["agents_executed"].append("sales")
            
            # Execute lead agent (parallel)
            lead_result = await self.agents["lead"].execute({})
            await self.context.set("lead_output", lead_result.output, "lead")
            self.active_runs[run_id]["agents_executed"].append("lead")
            
            # Execute risk agent
            risk_result = await self.agents["risk"].execute({
                "prospects": lead_result.output.get("leads", [])
            })
            await self.context.set("risk_output", risk_result.output, "risk")
            self.active_runs[run_id]["agents_executed"].append("risk")
            
            # Execute automation agent
            auto_result = await self.agents["automation"].execute({
                "offers": sales_result.output.get("offers", [])
            })
            await self.context.set("automation_output", auto_result.output, "automation")
            self.active_runs[run_id]["agents_executed"].append("automation")
            
            self.active_runs[run_id]["status"] = "completed"
            
            return {
                "run_id": run_id,
                "status": "completed",
                "agents_executed": self.active_runs[run_id]["agents_executed"],
                "context": await self.context.export(),
                "message_stats": self.broker.get_message_stats()
            }
        
        except Exception as e:
            self.active_runs[run_id]["status"] = "failed"
            self.active_runs[run_id]["error"] = str(e)
            return {
                "run_id": run_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def resume_from_approval(self, db: Session, approval: models.Approval) -> Dict[str, Any]:
        """Resume workflow after approval"""
        task_id = approval.task_id
        
        # Find active run or create new one
        run_id = f"run-resume-{id(self)}"
        self.active_runs[run_id] = {
            "task_id": task_id,
            "status": "running",
            "resumed_from_approval": approval.id
        }
        
        # Continue from where we left off
        # This would continue the workflow from the approval point
        return {
            "run_id": run_id,
            "status": "resumed",
            "approval_id": approval.id
        }
    
    def get_run_status(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a run"""
        return self.active_runs.get(run_id)
    
    def get_all_runs(self) -> List[Dict[str, Any]]:
        """Get all active runs"""
        return list(self.active_runs.values())
    
    async def get_context(self) -> Dict[str, Any]:
        """Get current shared context"""
        return await self.context.export()
    
    def get_broker_stats(self) -> Dict[str, Any]:
        """Get message broker statistics"""
        return self.broker.get_message_stats()


# Singleton instance
coordinator = AgentCoordinator()
