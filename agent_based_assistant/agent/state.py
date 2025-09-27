# State schema for agent-based visa assistant
# Purpose: Define the state structure for the React Agent following LangGraph documentation

from typing import Annotated, Any, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from operator import add

class AgentState(TypedDict):
    """
    State schema for the visa assistant React Agent.
    
    Based on LangGraph documentation patterns:
    - messages: List of conversation messages with add_messages reducer
    - Custom fields: Using Optional types for visa-specific data
    - Collection tracking: Fields to manage iterative data collection
    """
    
    # Core conversation messages (required for React Agent)
    messages: Annotated[list, add_messages]
    
    # Required by LangGraph's create_react_agent
    remaining_steps: Optional[int]
    
    # === Visa Application Data (from existing node-based workflow) ===
    
    # Initial basic information collection
    initial_info: Optional[dict[str, Any]]  # {"country": "thailand", "purpose_of_travel": "tourism", "number_of_travelers": 2, "travel_dates": "24/01/26 to 02/02/26"}
    
    # Detailed visa application data (accumulated via tools)
    personal_info: Annotated[list[dict[str, Any]], add]        # Name, DOB, nationality, address, phone, email
    passport_info: Annotated[list[dict[str, Any]], add]        # Passport number, issue date, expiry, place of issue
    travel_details: Annotated[list[dict[str, Any]], add]       # Entry/exit dates, purpose, duration, previous visits, num_travelers, destination
    employment_info: Annotated[list[dict[str, Any]], add]      # Job title, employer, salary, work address
    financial_info: Annotated[list[dict[str, Any]], add]       # Bank statements, income proof, sponsor details
    accommodation_info: Annotated[list[dict[str, Any]], add]   # Hotel bookings, invitation letters, host details
    document_uploads: Annotated[list[dict[str, Any]], add]     # Photos, certificates, medical reports
    emergency_contacts: Annotated[list[dict[str, Any]], add]   # Next of kin details
    insurance_info: Annotated[list[dict[str, Any]], add]       # Travel insurance details
    visa_details: Annotated[list[dict[str, Any]], add]         # Previous visa applications, refusals, visa_type
    
    # === Agent-specific Control Fields ===
    
    # Collection progress tracking
    collection_in_progress: Optional[bool]                     # True when actively collecting visa application data
    missing_fields: Optional[list[str]]                        # List of required fields still needed
    current_collection_stage: Optional[str]                    # "basic", "detailed", "documents", etc.
    
    # Session management
    incomplete_session_id: Optional[str]                       # For resuming incomplete applications
    
    # Error handling and retry logic
    extraction_retry_count: Optional[int]                      # Counter to prevent infinite retry loops
    last_extraction_error: Optional[str]                       # Store last extraction error for context
    
    # Agent decision tracking
    last_tool_used: Optional[str]                              # Track which tool was last called
    conversation_context: Optional[str]                        # "consultation", "application", "documents"
    
    # === Enhanced Scalability & Error Handling Fields ===
    
    # Session and performance management
    session_metadata: Optional[dict[str, Any]]                 # Timestamps, user_agent, request_count
    active_tools: Optional[list[str]]                          # Currently active tool calls
    tool_call_count: Optional[int]                             # Prevent infinite tool loops (reset each turn)
    error_history: Annotated[list[dict[str, Any]], add]        # Track recurring issues with timestamps
    
    # Multi-application support for scalability
    multiple_applications: Optional[dict[str, dict[str, Any]]] # {"thailand": {...}, "vietnam": {...}}
    primary_application: Optional[str]                         # Which country is current focus
    
    # Performance optimization
    cached_visa_info: Optional[dict[str, Any]]                 # Cache frequently requested country data
    conversation_summary: Optional[str]                        # Condensed history for long conversations
    state_version: Optional[int]                               # For conflict resolution and state validation


# === Input/Output Schemas for API exposure (following LangGraph patterns) ===

class VisaAgentInput(TypedDict):
    """
    Input schema for the visa agent API endpoint.
    Clean interface for external interactions.
    """
    message: str                                                # User's message/question
    session_id: Optional[str]                                   # For session persistence


class VisaAgentOutput(TypedDict):
    """
    Output schema for the visa agent API response.
    Structured response for frontend consumption.
    """
    response: str                                               # Agent's response message
    session_id: str                                             # Session identifier
    collection_status: Optional[str]                           # "incomplete", "basic_complete", "detailed_complete", etc.
    missing_fields: Optional[list[str]]                        # Fields still needed for application
    next_action: Optional[str]                                  # Suggested next action for user


# === State Validation & Utility Functions ===

def validate_agent_state(state: AgentState) -> tuple[bool, list[str]]:
    """
    Validate agent state for consistency and completeness.
    Returns (is_valid, list_of_issues)
    """
    issues = []
    
    # Check required fields
    if "messages" not in state:
        issues.append("Missing required 'messages' field")
    
    # Validate collection state consistency
    if state.get("collection_in_progress") and not state.get("initial_info"):
        issues.append("collection_in_progress=True but no initial_info")
    
    # Check retry count limits
    if state.get("extraction_retry_count", 0) > 3:
        issues.append("Extraction retry count exceeded maximum limit")
        
    # Validate tool call loop prevention
    if state.get("tool_call_count", 0) > 10:
        issues.append("Tool call count exceeded safety limit")
    
    return len(issues) == 0, issues


def create_error_record(error_type: str, error_message: str, tool_name: str = None) -> dict[str, Any]:
    """Create standardized error record for error_history"""
    import time
    return {
        "timestamp": time.time(),
        "error_type": error_type,
        "message": error_message,
        "tool": tool_name,
        "severity": "error"
    }


def reset_session_state(state: AgentState, keep_messages: bool = True) -> dict[str, Any]:
    """
    Reset state for fresh start while preserving conversation if needed.
    Used for error recovery and session cleanup.
    """
    fresh_state = {
        "initial_info": None,
        "collection_in_progress": False,
        "missing_fields": None,
        "extraction_retry_count": 0,
        "last_extraction_error": None,
        "conversation_context": None,
        "tool_call_count": 0,
        "state_version": (state.get("state_version", 0) + 1)
    }
    
    if keep_messages:
        fresh_state["messages"] = state.get("messages", [])
    
    return fresh_state


def get_application_progress(state: AgentState) -> dict[str, Any]:
    """
    Calculate application completion progress for UI display.
    Returns progress information and next steps.
    """
    progress = {
        "stage": "not_started",
        "completion_percentage": 0,
        "completed_sections": [],
        "next_required": []
    }
    
    if not state.get("initial_info"):
        return progress
    
    # Calculate completion based on collected data
    required_sections = ["initial_info", "personal_info", "passport_info", "travel_details"]
    completed = []
    
    for section in required_sections:
        if state.get(section):
            completed.append(section)
    
    progress.update({
        "stage": "in_progress" if completed else "basic_complete",
        "completion_percentage": (len(completed) / len(required_sections)) * 100,
        "completed_sections": completed,
        "next_required": [s for s in required_sections if s not in completed]
    })
    
    return progress