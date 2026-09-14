"""
Billing analytics and reporting
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict
from paos.billing.cost_tracker import CostEntry, CostType, ServiceCostCalculator


class BillingAnalytics:
    """Analytics for billing data"""
    
    def __init__(self):
        self.cost_entries: List[CostEntry] = []
    
    def add_cost(self, entry: CostEntry):
        """Add cost entry"""
        self.cost_entries.append(entry)
    
    def get_total_cost(
        self,
        task_id: Optional[str] = None,
        run_id: Optional[str] = None,
        cost_type: Optional[CostType] = None,
        days: Optional[int] = None
    ) -> Decimal:
        """Get total cost with optional filters"""
        entries = self._filter_entries(task_id, run_id, cost_type, days)
        return sum((entry.amount for entry in entries), Decimal("0"))
    
    def get_cost_breakdown_by_type(
        self,
        task_id: Optional[str] = None,
        days: Optional[int] = None
    ) -> Dict[str, Decimal]:
        """Get cost breakdown by type"""
        entries = self._filter_entries(task_id, None, None, days)
        breakdown = defaultdict(Decimal)
        
        for entry in entries:
            breakdown[entry.cost_type.value] += entry.amount
        
        return dict(breakdown)
    
    def get_cost_breakdown_by_service(
        self,
        task_id: Optional[str] = None,
        days: Optional[int] = None
    ) -> Dict[str, Decimal]:
        """Get cost breakdown by service"""
        entries = self._filter_entries(task_id, None, None, days)
        breakdown = defaultdict(Decimal)
        
        for entry in entries:
            service = entry.service or "unknown"
            breakdown[service] += entry.amount
        
        return dict(breakdown)
    
    def get_cost_by_agent(
        self,
        task_id: Optional[str] = None,
        days: Optional[int] = None
    ) -> Dict[str, Decimal]:
        """Get cost by agent"""
        entries = self._filter_entries(task_id, None, None, days)
        breakdown = defaultdict(Decimal)
        
        for entry in entries:
            agent = entry.metadata.get("agent", "unknown")
            breakdown[agent] += entry.amount
        
        return dict(breakdown)
    
    def get_hourly_cost_trend(
        self,
        task_id: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, Decimal]:
        """Get hourly cost trend"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        entries = [
            e for e in self.cost_entries
            if e.timestamp > cutoff and (task_id is None or e.task_id == task_id)
        ]
        
        trend = defaultdict(Decimal)
        for entry in entries:
            hour = entry.timestamp.strftime("%Y-%m-%d %H:00")
            trend[hour] += entry.amount
        
        return dict(sorted(trend.items()))
    
    def get_cost_efficiency(
        self,
        task_id: str,
        outcome_value: Decimal
    ) -> Dict[str, Any]:
        """Calculate cost efficiency (cost per value delivered)"""
        total_cost = self.get_total_cost(task_id=task_id)
        
        if outcome_value == 0:
            efficiency = Decimal("0")
        else:
            efficiency = total_cost / outcome_value
        
        return {
            "total_cost": float(total_cost),
            "outcome_value": float(outcome_value),
            "cost_per_unit_value": float(efficiency),
            "roi_percentage": float((outcome_value - total_cost) / outcome_value * 100) if outcome_value > 0 else 0
        }
    
    def get_top_cost_drivers(
        self,
        limit: int = 10,
        days: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get top cost drivers"""
        entries = self._filter_entries(None, None, None, days)
        
        # Sort by amount descending
        sorted_entries = sorted(entries, key=lambda e: e.amount, reverse=True)
        
        result = []
        for entry in sorted_entries[:limit]:
            result.append({
                "task_id": entry.task_id,
                "service": entry.service,
                "cost_type": entry.cost_type.value,
                "amount": float(entry.amount),
                "timestamp": entry.timestamp.isoformat()
            })
        
        return result
    
    def get_budget_summary(
        self,
        budget_limit: Decimal,
        days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get budget status"""
        total = self.get_total_cost(days=days)
        remaining = budget_limit - total
        used_percentage = (total / budget_limit * 100) if budget_limit > 0 else 0
        
        return {
            "budget_limit": float(budget_limit),
            "total_spent": float(total),
            "remaining": float(remaining),
            "used_percentage": float(used_percentage),
            "status": "warning" if used_percentage > 80 else "ok",
            "projected_daily_cost": float(total / (days or 1))
        }
    
    def _filter_entries(
        self,
        task_id: Optional[str] = None,
        run_id: Optional[str] = None,
        cost_type: Optional[CostType] = None,
        days: Optional[int] = None
    ) -> List[CostEntry]:
        """Filter cost entries"""
        entries = self.cost_entries
        
        if task_id:
            entries = [e for e in entries if e.task_id == task_id]
        
        if run_id:
            entries = [e for e in entries if e.run_id == run_id]
        
        if cost_type:
            entries = [e for e in entries if e.cost_type == cost_type]
        
        if days:
            cutoff = datetime.utcnow() - timedelta(days=days)
            entries = [e for e in entries if e.timestamp > cutoff]
        
        return entries
    
    def export_report(
        self,
        task_id: Optional[str] = None,
        days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Export comprehensive billing report"""
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "period_days": days,
            "task_id": task_id,
            "total_cost": float(self.get_total_cost(task_id=task_id, days=days)),
            "by_type": {k: float(v) for k, v in self.get_cost_breakdown_by_type(task_id, days).items()},
            "by_service": {k: float(v) for k, v in self.get_cost_breakdown_by_service(task_id, days).items()},
            "by_agent": {k: float(v) for k, v in self.get_cost_by_agent(task_id, days).items()},
            "top_drivers": self.get_top_cost_drivers(limit=10, days=days),
            "hourly_trend": {k: float(v) for k, v in self.get_hourly_cost_trend(task_id).items()}
        }


# Singleton instance
billing_analytics = BillingAnalytics()
