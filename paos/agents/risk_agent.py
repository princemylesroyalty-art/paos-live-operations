"""
Lead Agent - Identifies and qualifies leads
"""

from paos.agents.base_agent import BaseAgent, ToolDefinition
from typing import Dict, Any
import asyncio


class LeadAgent(BaseAgent):
    """Lead agent for prospect identification"""
    
    def __init__(self):
        super().__init__(
            name="Lead Agent",
            description="Identifies and qualifies potential customers.",
            model="gpt-4",
            temperature=0.5
        )
        
        self.register_tool(ToolDefinition(
            name="identify_leads",
            description="Identify potential leads",
            func=self._identify_leads,
            requires_approval=False
        ))
        
        self.register_tool(ToolDefinition(
            name="qualify_leads",
            description="Qualify leads by criteria",
            func=self._qualify_leads,
            requires_approval=False
        ))
    
    async def _identify_leads(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Identify potential leads"""
        await asyncio.sleep(0.3)
        return {
            "leads_identified": 50,
            "leads": [
                {"id": i, "name": f"Prospect {i}", "industry": "Tech", "fit_score": 0.8}
                for i in range(1, 26)
            ]
        }
    
    async def _qualify_leads(self, leads: list) -> Dict[str, Any]:
        """Qualify leads"""
        await asyncio.sleep(0.3)
        qualified = [l for l in leads if l.get("fit_score", 0) > 0.7]
        return {
            "total_leads": len(leads),
            "qualified_leads": len(qualified),
            "leads": qualified
        }
