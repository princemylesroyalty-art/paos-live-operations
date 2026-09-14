"""
Approval rule engine for context-aware workflows
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime, time
from enum import Enum
from paos import models


class RuleDecision(Enum):
    """Rule evaluation outcome"""
    APPROVE = "approve"
    REJECT = "reject"
    CONDITIONAL = "conditional"
    ESCALATE = "escalate"


class ApprovalDecision:
    """Result of approval evaluation"""
    
    def __init__(
        self,
        decision: RuleDecision,
        reason: str,
        rule_name: str,
        requires_human: bool = False,
        conditions: Optional[List[str]] = None
    ):
        self.decision = decision
        self.reason = reason
        self.rule_name = rule_name
        self.requires_human = requires_human
        self.conditions = conditions or []
        self.timestamp = datetime.utcnow()


class ApprovalRule(ABC):
    """Base approval rule"""
    
    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled
    
    @abstractmethod
    async def evaluate(self, task: models.Task, action: str) -> ApprovalDecision:
        """Evaluate if approval is needed"""
        pass
    
    def applies_to(self, action: str) -> bool:
        """Check if rule applies to action"""
        return True


class AmountThresholdRule(ApprovalRule):
    """Require approval if amount exceeds threshold"""
    
    def __init__(self, name: str, threshold: float, currency: str = "USD"):
        super().__init__(name)
        self.threshold = threshold
        self.currency = currency
    
    async def evaluate(self, task: models.Task, action: str) -> ApprovalDecision:
        if not self.enabled:
            return ApprovalDecision(
                RuleDecision.APPROVE,
                "Rule disabled",
                self.name
            )
        
        amount = task.input_data.get("amount", 0)
        if amount > self.threshold:
            return ApprovalDecision(
                RuleDecision.CONDITIONAL,
                f"Amount ${amount} exceeds threshold ${self.threshold}",
                self.name,
                requires_human=True
            )
        
        return ApprovalDecision(
            RuleDecision.APPROVE,
            f"Amount ${amount} within threshold",
            self.name
        )
    
    def applies_to(self, action: str) -> bool:
        return action in ["purchase", "payment", "transfer", "financial"]


class TimeWindowRule(ApprovalRule):
    """Only allow actions during business hours"""
    
    def __init__(self, name: str, start_time: str = "09:00", end_time: str = "17:00"):
        super().__init__(name)
        self.start_time = datetime.strptime(start_time, "%H:%M").time()
        self.end_time = datetime.strptime(end_time, "%H:%M").time()
    
    async def evaluate(self, task: models.Task, action: str) -> ApprovalDecision:
        if not self.enabled:
            return ApprovalDecision(
                RuleDecision.APPROVE,
                "Rule disabled",
                self.name
            )
        
        current_time = datetime.utcnow().time()
        if self.start_time <= current_time <= self.end_time:
            return ApprovalDecision(
                RuleDecision.APPROVE,
                f"Within business hours ({self.start_time} - {self.end_time})",
                self.name
            )
        
        return ApprovalDecision(
            RuleDecision.CONDITIONAL,
            f"Outside business hours (current: {current_time})",
            self.name,
            requires_human=True
        )
    
    def applies_to(self, action: str) -> bool:
        return action in ["communicate", "send_email", "call_customer"]


class RiskScoreRule(ApprovalRule):
    """Require approval if risk score exceeds threshold"""
    
    def __init__(self, name: str, threshold: float = 0.7):
        super().__init__(name)
        self.threshold = threshold
    
    async def evaluate(self, task: models.Task, action: str) -> ApprovalDecision:
        if not self.enabled:
            return ApprovalDecision(
                RuleDecision.APPROVE,
                "Rule disabled",
                self.name
            )
        
        risk_score = task.input_data.get("risk_score", 0)
        if risk_score > self.threshold:
            return ApprovalDecision(
                RuleDecision.CONDITIONAL,
                f"Risk score {risk_score} exceeds threshold {self.threshold}",
                self.name,
                requires_human=True
            )
        
        return ApprovalDecision(
            RuleDecision.APPROVE,
            f"Risk score {risk_score} acceptable",
            self.name
        )
    
    def applies_to(self, action: str) -> bool:
        return action in ["financial", "purchase", "partnership"]


class FrequencyCapRule(ApprovalRule):
    """Limit actions per time period"""
    
    def __init__(self, name: str, max_per_hour: int = 10, max_per_day: int = 100):
        super().__init__(name)
        self.max_per_hour = max_per_hour
        self.max_per_day = max_per_day
        self.call_history: List[datetime] = []
    
    async def evaluate(self, task: models.Task, action: str) -> ApprovalDecision:
        if not self.enabled:
            return ApprovalDecision(
                RuleDecision.APPROVE,
                "Rule disabled",
                self.name
            )
        
        now = datetime.utcnow()
        
        # Count calls in last hour
        hour_ago = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        calls_this_hour = sum(1 for t in self.call_history if t > hour_ago)
        
        if calls_this_hour >= self.max_per_hour:
            return ApprovalDecision(
                RuleDecision.REJECT,
                f"Hourly limit reached ({calls_this_hour}/{self.max_per_hour})",
                self.name,
                requires_human=False
            )
        
        # Count calls in last day
        day_ago = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        calls_today = sum(1 for t in self.call_history if t > day_ago)
        
        if calls_today >= self.max_per_day:
            return ApprovalDecision(
                RuleDecision.REJECT,
                f"Daily limit reached ({calls_today}/{self.max_per_day})",
                self.name,
                requires_human=True
            )
        
        self.call_history.append(now)
        return ApprovalDecision(
            RuleDecision.APPROVE,
            f"Within limits (hour: {calls_this_hour}/{self.max_per_hour}, day: {calls_today}/{self.max_per_day})",
            self.name
        )
    
    def applies_to(self, action: str) -> bool:
        return action in ["communicate", "send_email", "api_call"]


class ComplianceRule(ApprovalRule):
    """Check compliance requirements"""
    
    def __init__(self, name: str, required_regulations: List[str]):
        super().__init__(name)
        self.required_regulations = required_regulations
    
    async def evaluate(self, task: models.Task, action: str) -> ApprovalDecision:
        if not self.enabled:
            return ApprovalDecision(
                RuleDecision.APPROVE,
                "Rule disabled",
                self.name
            )
        
        task_regulations = task.input_data.get("regulations", [])
        
        missing = [r for r in self.required_regulations if r not in task_regulations]
        if missing:
            return ApprovalDecision(
                RuleDecision.CONDITIONAL,
                f"Missing compliance checks: {', '.join(missing)}",
                self.name,
                requires_human=True,
                conditions=missing
            )
        
        return ApprovalDecision(
            RuleDecision.APPROVE,
            f"All compliance requirements met: {', '.join(self.required_regulations)}",
            self.name
        )
    
    def applies_to(self, action: str) -> bool:
        return action in ["financial", "data_access", "partnership"]
