"""
Cost tracking for operations
"""

from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum


class CostType(str, Enum):
    """Types of costs"""
    API_CALL = "api_call"
    AGENT_EXECUTION = "agent_execution"
    DATA_STORAGE = "data_storage"
    COMMUNICATION = "communication"
    AUTOMATION = "automation"
    OTHER = "other"


class CostEntry:
    """Individual cost entry"""
    
    def __init__(
        self,
        task_id: str,
        run_id: str,
        cost_type: CostType,
        amount: Decimal,
        currency: str = "USD",
        service: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.task_id = task_id
        self.run_id = run_id
        self.cost_type = cost_type
        self.amount = amount
        self.currency = currency
        self.service = service
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
        self.id = f"{task_id}-{run_id}-{id(self)}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "run_id": self.run_id,
            "cost_type": self.cost_type.value,
            "amount": float(self.amount),
            "currency": self.currency,
            "service": self.service,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class ServiceCostCalculator:
    """Calculate costs for external services"""
    
    # Pricing per service
    PRICING = {
        "openai": {
            "gpt-4": {"input": 0.03, "output": 0.06},  # per 1K tokens
            "gpt-3.5": {"input": 0.0015, "output": 0.002},
        },
        "anthropic": {
            "claude-3": {"input": 0.003, "output": 0.015},  # per 1K tokens
        },
        "email": {"send": 0.001, "receive": 0.0001},
        "sms": {"send": 0.05, "receive": 0.01},
        "storage": {"gb_month": 0.023},  # AWS S3 pricing
    }
    
    @staticmethod
    def calculate_api_cost(
        service: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> Decimal:
        """Calculate API call cost"""
        if service not in ServiceCostCalculator.PRICING:
            return Decimal("0")
        
        if model not in ServiceCostCalculator.PRICING[service]:
            return Decimal("0")
        
        pricing = ServiceCostCalculator.PRICING[service][model]
        input_cost = (input_tokens / 1000) * pricing.get("input", 0)
        output_cost = (output_tokens / 1000) * pricing.get("output", 0)
        
        return Decimal(str(input_cost + output_cost))
    
    @staticmethod
    def calculate_communication_cost(method: str, count: int) -> Decimal:
        """Calculate communication cost"""
        pricing = ServiceCostCalculator.PRICING.get("email", {})
        if method == "email":
            return Decimal(str(pricing.get("send", 0) * count))
        elif method == "sms":
            pricing = ServiceCostCalculator.PRICING.get("sms", {})
            return Decimal(str(pricing.get("send", 0) * count))
        
        return Decimal("0")
    
    @staticmethod
    def calculate_storage_cost(gb: float, months: int = 1) -> Decimal:
        """Calculate storage cost"""
        pricing = ServiceCostCalculator.PRICING["storage"]["gb_month"]
        return Decimal(str(gb * months * pricing))
    
    @staticmethod
    def calculate_agent_execution_cost(duration_seconds: float) -> Decimal:
        """Calculate agent execution cost (estimated)"""
        # $0.01 per minute of agent execution
        minutes = duration_seconds / 60
        return Decimal(str(minutes * 0.01))
