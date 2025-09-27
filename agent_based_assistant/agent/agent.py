# React Agent setup for visa assistant
# Purpose: Create the main agent using LangGraph's create_react_agent with streaming support

from typing import Any, Dict, List, AsyncGenerator
from langchain_core.messages import AnyMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph
from langgraph.prebuilt.chat_agent_executor import AgentState

from agent.state import AgentState as VisaAgentState, validate_agent_state, create_error_record
from agent.prompts import get_system_prompt
from config.settings import llm, stream_llm_safe, app_config
from tools.greetings import greetings_tool
from tools.visa_information import general_enquiry_tool  
from tools.application_basic import base_information_collector_tool
from tools.visa_type_analyzer import visa_type_analyzer_tool
from tools.application_detailed import application_detailed_tool
from tools.document_processing import document_processing_tool
from tools.session_management import session_management_tool


class VisaAssistantAgent:
    """
    Main visa assistant agent using LangGraph's React Agent pattern.
    Handles tool selection, state management, and streaming responses.
    """
    
    def __init__(self):
        self.tools = self._initialize_tools()
        self.agent = self._create_agent()
        
    def _initialize_tools(self) -> List:
        """Initialize all available tools for the agent"""
        return [
            greetings_tool,
            general_enquiry_tool,
            base_information_collector_tool,
            visa_type_analyzer_tool,
            application_detailed_tool,
            document_processing_tool,
            session_management_tool
        ]
    
    def _create_agent(self):
        """Create the React Agent with custom state and prompt"""
        
        def custom_prompt(state: VisaAgentState) -> List[AnyMessage]:
            """
            Generate system prompt based on current state context.
            Provides agent with context-aware instructions.
            """
            # Validate state before processing
            is_valid, issues = validate_agent_state(state)
            if not is_valid:
                print(f"State validation issues: {issues}")
            
            # Get base system prompt
            system_prompt = get_system_prompt(state)
            
            # Add system message to conversation
            messages = [SystemMessage(content=system_prompt)]
            
            # Add conversation history
            if state.get("messages"):
                messages.extend(state["messages"])
            
            return messages
        
        # Create React Agent with custom state schema
        agent = create_react_agent(
            model=llm,
            tools=self.tools,
            state_schema=VisaAgentState,
            prompt=custom_prompt
        )
        
        return agent
    
    def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke agent with state validation and error handling.
        Non-streaming version for simple interactions.
        """
        try:
            # Prepare state with safety checks
            state = self._prepare_state(input_data)
            
            # Invoke agent
            result = self.agent.invoke(state)
            
            # Validate and clean result
            return self._process_result(result)
            
        except Exception as e:
            print(f"Agent invocation error: {e}")
            return self._handle_agent_error(input_data, str(e))
    
    async def stream(self, input_data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream agent responses for real-time UI updates.
        Yields state updates as they occur.
        """
        try:
            # Prepare state
            state = self._prepare_state(input_data)
            
            # Stream with messages mode for token-level streaming (following LangGraph docs)
            async for message_chunk, metadata in self.agent.astream(state, stream_mode="messages"):
                processed_chunk = self._process_message_chunk(message_chunk, metadata)
                if processed_chunk:
                    yield processed_chunk
                    
        except Exception as e:
            print(f"Agent streaming error: {e}")
            yield self._handle_stream_error(input_data, str(e))
    
    def _prepare_state(self, input_data: Dict[str, Any]) -> VisaAgentState:
        """
        Prepare and validate state from input data.
        Ensures state consistency and adds required fields.
        """
        # Start with base state structure
        state = VisaAgentState({
            "messages": input_data.get("messages", []),
            "tool_call_count": 0,
            "state_version": 1
        })
        
        # Merge additional state fields if provided
        for key, value in input_data.items():
            if key in VisaAgentState.__annotations__ and value is not None:
                state[key] = value
        
        # Validate prepared state
        is_valid, issues = validate_agent_state(state)
        if not is_valid:
            print(f"State preparation issues: {issues}")
            # Could implement auto-correction here
        
        return state
    
    def _process_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and validate agent result.
        Ensures result contains required fields and clean data.
        """
        # Extract key information for response
        processed = {
            "messages": result.get("messages", []),
            "session_id": result.get("session_id"),
            "collection_status": self._determine_collection_status(result),
            "missing_fields": result.get("missing_fields"),
            "conversation_context": result.get("conversation_context")
        }
        
        # Get latest assistant message for response
        if processed["messages"]:
            for msg in reversed(processed["messages"]):
                if hasattr(msg, 'type') and msg.type == 'ai':
                    processed["response"] = msg.content
                    break
        
        return processed
    
    def _process_message_chunk(self, message_chunk, metadata) -> Dict[str, Any]:
        """
        Process message chunks following LangGraph documentation pattern.
        Input: message_chunk (the token/message), metadata (graph info)
        """
        # Process message chunks from agent node only (LangGraph official pattern)
        # OLD WORKING CODE (COMMENTED OUT):
        # # Check if this is an AI message with content (following LangGraph docs)
        # if hasattr(message_chunk, 'content') and message_chunk.content:
        #     # Only process non-empty string content
        #     if isinstance(message_chunk.content, str) and message_chunk.content.strip():
        #         return {
        #             "token": message_chunk.content,
        #             "type": "token",
        #             "metadata": metadata
        #         }
        # 
        # # Skip everything else (tool calls, empty content, etc.)
        # return None
        
        # LANGRAPH OFFICIAL FILTERING - Use metadata to filter by node
        # Only process messages from 'agent' node, skip 'tools' node (prevents duplication)
        if metadata.get('langgraph_node') != 'agent':
            return None  # Skip tool responses and other nodes
        
        # Process AI message content from agent node only
        if hasattr(message_chunk, 'content') and message_chunk.content:
            # Handle list format: [{'text': 'Hello!', 'type': 'text', 'index': 0}]
            if isinstance(message_chunk.content, list) and len(message_chunk.content) > 0:
                text_item = message_chunk.content[0]
                if isinstance(text_item, dict) and text_item.get('type') == 'text':
                    text_content = text_item.get('text', '')
                    if text_content and text_content.strip():
                        return {
                            "token": text_content,
                            "type": "token",
                            "metadata": metadata
                        }
            # Handle string format (fallback)
            elif isinstance(message_chunk.content, str) and message_chunk.content.strip():
                return {
                    "token": message_chunk.content,
                    "type": "token",
                    "metadata": metadata
                }
        
        # Skip everything else (empty content, tool setup chunks, etc.)
        return None
    
    def _determine_collection_status(self, state: Dict[str, Any]) -> str:
        """Determine current collection status based on state"""
        if not state.get("initial_info"):
            return "not_started"
        elif state.get("collection_in_progress"):
            return "in_progress"
        elif state.get("personal_info") and state.get("passport_info"):
            return "detailed_complete"
        elif state.get("initial_info"):
            return "basic_complete"
        else:
            return "incomplete"
    
    def _handle_agent_error(self, input_data: Dict[str, Any], error_msg: str) -> Dict[str, Any]:
        """Handle agent errors gracefully with user-friendly responses"""
        return {
            "response": "I'm experiencing some technical difficulties. Let me try to help you in a different way. What can I assist you with regarding your visa needs?",
            "error": True,
            "error_message": error_msg,
            "session_id": input_data.get("session_id"),
            "collection_status": "error"
        }
    
    def _handle_stream_error(self, input_data: Dict[str, Any], error_msg: str) -> Dict[str, Any]:
        """Handle streaming errors gracefully"""
        return {
            "response": "I encountered an issue while processing your request. Please try again.",
            "error": True,
            "error_message": error_msg,
            "type": "error"
        }


# Global agent instance
visa_agent = VisaAssistantAgent()

# Export functions for external use
def invoke_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke the visa agent with input data"""
    return visa_agent.invoke(input_data)

async def stream_agent(input_data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
    """Stream visa agent responses"""
    async for chunk in visa_agent.stream(input_data):
        yield chunk