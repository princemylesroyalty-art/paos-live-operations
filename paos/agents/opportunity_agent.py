"""
Opportunity Agent - Filters and validates opportunities
"""

from paos.agents.base_agent import BaseAgent, ToolDefinition
from typing import Dict, Any
import asyncio


class OpportunityAgent(BaseAgent):
    """Opportunity agent for filtering and scoring"""
    
    def __init__(self):
        super().__init__(
            name="Opportunity Agent",
            description="Filters opportunities based on profit potential and feasibility.",
            model="gpt-4",
            temperature=0.4
        )
        
        self.register_tool(ToolDefinition(
            name="filter_by_profit",
            description="Filter opportunities by profit potential",
            func=self._filter_by_profit,
            requires_approval=False
        ))
        
        self.register_tool(ToolDefinition(
            name="score_opportunities",
            description="Score opportunities for feasibility",
            func=self._score_opportunities,
            requires_approval=False
        ))
    
    async def _filter_by_profit(self, opportunities: list, min_profit: float = 1000) -> Dict[str, Any]:
        """Filter by profit threshold"""
        await asyncio.sleep(0.3)
        filtered = [op for op in opportunities if op.get("profit", 0) > min_profit]
        return {
            "input_count": len(opportunities),
            "filtered_count": len(filtered),
            "opportunities": filtered
        }
    
    async def _score_opportunities(self, opportunities: list) -> Dict[str, Any]:
        """Score opportunities"""
        await asyncio.sleep(0.3)
        scored = []
        for op in opportunities:
            op["score"] = 0.8  # Simulated score
            scored.append(op)
        
        return {
            "total_scored": len(scored),
            "top_opportunities": sorted(scored, key=lambda x: x.get("score", 0), reverse=True)[:10]
        }
