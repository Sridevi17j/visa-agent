# Placeholder for detailed application tool
from typing import Any, Dict
from langchain_core.tools import tool
from agent.state import AgentState

@tool
def application_detailed_tool(user_message: str, state: AgentState) -> Dict[str, Any]:
    """Placeholder tool for detailed application collection"""
    return {
        "response": "Detailed application tool is not implemented yet.",
        "last_tool_used": "application_detailed"
    }

__all__ = ["application_detailed_tool"]