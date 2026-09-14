"""
Sales Agent - Generates offers
"""

from paos.agents.base_agent import BaseAgent, ToolDefinition
from typing import Dict, Any
import asyncio


class SalesAgent(BaseAgent):
    """Sales agent for offer generation"""
    
    def __init__(self):
        super().__init__(
            name="Sales Agent",
            description="Creates compelling offers and sales strategies.",
            model="gpt-4",
            temperature=0.6
        )
        
        self.register_tool(ToolDefinition(
            name="generate_offer",
            description="Generate sales offer",
            func=self._generate_offer,
            requires_approval=False
        ))
        
        self.register_tool(ToolDefinition(
            name="create_pitch",
            description="Create sales pitch",
            func=self._create_pitch,
            requires_approval=True,
            approval_level="communicate"
        ))
    
    async def _generate_offer(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Generate offer"""
        await asyncio.sleep(0.3)
        return {
            "offer_id": f"OFF-{opportunity.get('id')}",
            "base_price": 5000,
            "discount": 10,
            "final_price": 4500,
            "validity_days": 30
        }
    
    async def _create_pitch(self, offer: Dict[str, Any]) -> Dict[str, Any]:
        """Create sales pitch (requires approval)"""
        await asyncio.sleep(0.3)
        return {
            "pitch": "Exclusive limited-time offer for our premium service",
            "offer_id": offer.get("offer_id"),
            "status": "ready_to_send"
        }
