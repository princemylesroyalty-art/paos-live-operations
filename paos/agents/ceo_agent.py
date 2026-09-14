"""
CEO Agent - Task router and orchestrator
"""

from paos.agents.base_agent import BaseAgent, ToolDefinition, AgentState
from typing import Dict, Any


class CEOAgent(BaseAgent):
    """CEO agent that routes tasks to other agents"""
    
    def __init__(self):
        super().__init__(
            name="CEO Agent",
            description="Strategic task router. Analyzes incoming requests and routes to appropriate agents.",
            model="gpt-4",
            temperature=0.3  # Lower temp for strategic decisions
        )
        
        # Register tools
        self.register_tool(ToolDefinition(
            name="route_to_research",
            description="Route task to Research Agent for market analysis",
            func=self._route_to_research,
            requires_approval=False
        ))
        
        self.register_tool(ToolDefinition(
            name="route_to_opportunity",
            description="Route task to Opportunity Agent for filtering",
            func=self._route_to_opportunity,
            requires_approval=False
        ))
        
        self.register_tool(ToolDefinition(
            name="route_to_sales",
            description="Route task to Sales Agent for offer generation",
            func=self._route_to_sales,
            requires_approval=False
        ))
    
    async def _route_to_research(self, query: str, market: str) -> Dict[str, Any]:
        """Route to Research Agent"""
        return {
            "agent": "research",
            "task": "market_research",
            "query": query,
            "market": market
        }
    
    async def _route_to_opportunity(self, opportunities: list, filters: dict) -> Dict[str, Any]:
        """Route to Opportunity Agent"""
        return {
            "agent": "opportunity",
            "task": "filter_opportunities",
            "opportunities": opportunities,
            "filters": filters
        }
    
    async def _route_to_sales(self, opportunities: list) -> Dict[str, Any]:
        """Route to Sales Agent"""
        return {
            "agent": "sales",
            "task": "generate_offers",
            "opportunities": opportunities
        }
