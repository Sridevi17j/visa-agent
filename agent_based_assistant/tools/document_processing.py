# Placeholder for document processing tool
from typing import Any, Dict
from langchain_core.tools import tool
from agent.state import AgentState

@tool
def document_processing_tool(user_message: str, state: AgentState) -> Dict[str, Any]:
    """Placeholder tool for document processing"""
    return {
        "response": "Document processing tool is not implemented yet.",
        "last_tool_used": "document_processing"
    }

__all__ = ["document_processing_tool"]