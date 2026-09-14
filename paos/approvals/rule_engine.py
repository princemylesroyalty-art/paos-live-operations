"""
Approval rule engine
"""

from typing import List, Dict, Any, Optional
from paos.approvals.rules import ApprovalRule, ApprovalDecision, RuleDecision
from paos import models
from sqlalchemy.orm import Session


class ApprovalRuleEngine:
    """Evaluates approval rules and combines decisions"""
    
    def __init__(self):
        self.rules: Dict[str, ApprovalRule] = {}
        self.decision_history: List[Dict[str, Any]] = []
    
    def register_rule(self, rule: ApprovalRule):
        """Register an approval rule"""
        self.rules[rule.name] = rule
    
    def unregister_rule(self, rule_name: str):
        """Unregister a rule"""
        if rule_name in self.rules:
            del self.rules[rule_name]
    
    def get_rule(self, rule_name: str) -> Optional[ApprovalRule]:
        """Get a rule by name"""
        return self.rules.get(rule_name)
    
    def list_rules(self) -> List[ApprovalRule]:
        """List all registered rules"""
        return list(self.rules.values())
    
    async def evaluate(self, task: models.Task, action: str) -> Dict[str, Any]:
        """Evaluate all applicable rules"""
        decisions: List[ApprovalDecision] = []
        
        # Get applicable rules
        applicable_rules = [
            rule for rule in self.rules.values()
            if rule.enabled and rule.applies_to(action)
        ]
        
        # Evaluate each rule
        for rule in applicable_rules:
            decision = await rule.evaluate(task, action)
            decisions.append(decision)
        
        # Combine decisions
        combined = self._combine_decisions(decisions, action)
        
        # Store history
        self.decision_history.append({
            "task_id": task.id,
            "action": action,
            "timestamp": combined["timestamp"],
            "decisions": [d.__dict__ for d in decisions],
            "final_decision": combined["final_decision"],
            "requires_approval": combined["requires_approval"]
        })
        
        return combined
    
    def _combine_decisions(self, decisions: List[ApprovalDecision], action: str) -> Dict[str, Any]:
        """Combine multiple decisions using voting"""
        from datetime import datetime
        
        if not decisions:
            return {
                "final_decision": RuleDecision.APPROVE,
                "requires_approval": False,
                "reason": "No rules applied",
                "timestamp": datetime.utcnow(),
                "rules_applied": 0
            }
        
        # Decision priority: REJECT > ESCALATE > CONDITIONAL > APPROVE
        priority = {
            RuleDecision.REJECT: 4,
            RuleDecision.ESCALATE: 3,
            RuleDecision.CONDITIONAL: 2,
            RuleDecision.APPROVE: 1
        }
        
        # Get highest priority decision
        final_decision = max(decisions, key=lambda d: priority[d.decision])
        
        requires_approval = final_decision.decision in [
            RuleDecision.CONDITIONAL,
            RuleDecision.ESCALATE
        ] or final_decision.requires_human
        
        return {
            "final_decision": final_decision.decision.value,
            "requires_approval": requires_approval,
            "reason": final_decision.reason,
            "rule_name": final_decision.rule_name,
            "timestamp": final_decision.timestamp,
            "rules_applied": len(decisions),
            "all_decisions": [{
                "rule": d.rule_name,
                "decision": d.decision.value,
                "reason": d.reason,
                "requires_human": d.requires_human
            } for d in decisions]
        }
    
    def get_history(
        self,
        task_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get decision history"""
        history = self.decision_history
        
        if task_id:
            history = [h for h in history if h["task_id"] == task_id]
        
        if action:
            history = [h for h in history if h["action"] == action]
        
        return history[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get approval statistics"""
        total = len(self.decision_history)
        if not total:
            return {"total_decisions": 0}
        
        approved = sum(1 for h in self.decision_history if not h["requires_approval"])
        rejected = sum(1 for h in self.decision_history if h["final_decision"] == RuleDecision.REJECT.value)
        conditional = sum(1 for h in self.decision_history if h["requires_approval"])
        
        return {
            "total_decisions": total,
            "approved": approved,
            "rejected": rejected,
            "requiring_approval": conditional,
            "approval_rate": (conditional / total) * 100 if total > 0 else 0,
            "approval_rate": (approved / total) * 100 if total > 0 else 0,
        }


# Singleton instance
rule_engine = ApprovalRuleEngine()
