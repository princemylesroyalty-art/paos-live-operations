"""
Base agent class with LangGraph support
"""

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
import json


class AgentState(BaseModel):
    """State object passed through agent workflow"""
    input: Dict[str, Any]
    thoughts: List[str] = []
    tools_used: List[Dict[str, Any]] = []
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    approval_required: bool = False
    approval_reason: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True


class ToolDefinition(BaseModel):
    """Definition of a tool an agent can use"""
    name: str
    description: str
    func: Callable
    requires_approval: bool = False
    approval_level: Optional[str] = None


class BaseAgent:
    """Base agent class with LangGraph integration"""
    
    def __init__(self, name: str, description: str, model: str = "gpt-4", temperature: float = 0.7):
        self.name = name
        self.description = description
        self.model = model
        self.temperature = temperature
        self.llm = ChatOpenAI(model_name=model, temperature=temperature)
        self.tools: Dict[str, ToolDefinition] = {}
        self.graph = None
        self._build_graph()
    
    def register_tool(self, tool: ToolDefinition):
        """Register a tool this agent can use"""
        self.tools[tool.name] = tool
    
    def _build_graph(self):
        """Build LangGraph workflow"""
        self.graph = StateGraph(AgentState)
        
        # Add nodes
        self.graph.add_node("think", self._think_node)
        self.graph.add_node("execute", self._execute_node)
        self.graph.add_node("check_approval", self._check_approval_node)
        self.graph.add_node("finalize", self._finalize_node)
        
        # Add edges
        self.graph.add_edge("think", "execute")
        self.graph.add_edge("execute", "check_approval")
        self.graph.add_conditional_edges(
            "check_approval",
            self._approval_router,
            {"needs_approval": "finalize", "approved": "finalize", "end": END}
        )
        self.graph.add_edge("finalize", END)
        
        # Set entry point
        self.graph.set_entry_point("think")
        
        self.compiled_graph = self.graph.compile()
    
    async def _think_node(self, state: AgentState) -> AgentState:
        """Agent thinking/reasoning step"""
        prompt = f"""
You are {self.name}. {self.description}

Task: {json.dumps(state.input)}

What do you think about this task? What approach will you take?
Respond with your reasoning.
"""
        
        response = await self.llm.agenerate([prompt])
        thought = response.generations[0][0].text
        state.thoughts.append(thought)
        return state
    
    async def _execute_node(self, state: AgentState) -> AgentState:
        """Execute tools based on thinking"""
        # Parse which tools to use from thoughts
        prompt = f"""
Based on your thoughts: {state.thoughts[-1]}

Which tools would you use? Return JSON:
{{
    "tools": ["tool_name"],
    "parameters": {{}}
}}
"""
        
        response = await self.llm.agenerate([prompt])
        try:
            tool_plan = json.loads(response.generations[0][0].text)
            for tool_name in tool_plan.get("tools", []):
                if tool_name in self.tools:
                    tool = self.tools[tool_name]
                    result = await tool.func(**tool_plan.get("parameters", {}))
                    state.tools_used.append({
                        "tool": tool_name,
                        "requires_approval": tool.requires_approval,
                        "result": result
                    })
        except json.JSONDecodeError:
            state.error = "Failed to parse tool plan"
        
        return state
    
    def _check_approval_node(self, state: AgentState) -> AgentState:
        """Check if any tools require approval"""
        for tool_use in state.tools_used:
            if tool_use.get("requires_approval"):
                state.approval_required = True
                state.approval_reason = f"Tool '{tool_use['tool']}' requires approval"
                break
        return state
    
    def _approval_router(self, state: AgentState) -> str:
        """Route based on approval status"""
        if state.approval_required:
            return "needs_approval"
        return "approved"
    
    async def _finalize_node(self, state: AgentState) -> AgentState:
        """Finalize and generate output"""
        prompt = f"""
Based on:
Thoughts: {json.dumps(state.thoughts)}
Tools used: {json.dumps(state.tools_used)}

Generate final output as JSON.
"""
        
        response = await self.llm.agenerate([prompt])
        try:
            state.output = json.loads(response.generations[0][0].text)
        except json.JSONDecodeError:
            state.output = {"result": response.generations[0][0].text}
        
        return state
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentState:
        """Execute the agent workflow"""
        initial_state = AgentState(input=input_data)
        final_state = await self.compiled_graph.ainvoke(initial_state)
        return final_state
