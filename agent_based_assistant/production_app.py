from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import uuid
import json
from langchain_core.messages import HumanMessage

# Import agent-based system
from agent.agent import stream_agent, invoke_agent
from agent.state import AgentState

# Global state management for threads
thread_states = {}

def _extract_clean_content(content) -> str:
    """Extract clean text content from potentially complex message content"""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        # Handle list format like [{'text': 'Hello!', 'type': 'text'}]
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                if 'text' in item:
                    text_parts.append(str(item['text']))
                elif 'content' in item:
                    text_parts.append(str(item['content']))
                else:
                    # Fallback to string representation
                    text_parts.append(str(item))
            else:
                text_parts.append(str(item))
        return ' '.join(text_parts)
    elif isinstance(content, dict):
        # Handle dict format like {'text': 'Hello!', 'type': 'text'}
        if 'text' in content:
            return str(content['text'])
        elif 'content' in content:
            return str(content['content'])
        else:
            # Fallback to string representation
            return str(content)
    else:
        # Fallback for any other type
        return str(content)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("✅ Agent-based Visa Assistant Production Server initialized")
    yield
    # Shutdown
    print("🔄 Server shutdown")

app = FastAPI(
    title="Agent-based Visa Agent API",
    description="Production Agent-based Visa Assistant using LangGraph React Agent",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class MessageRequest(BaseModel):
    messages: List[Dict[str, Any]]

class ThreadResponse(BaseModel):
    thread_id: str

class RunResponse(BaseModel):
    messages: List[Dict[str, Any]]

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "agent-based-visa-agent"}

# LangGraph React SDK compatible endpoints
@app.get("/assistants/{assistant_id}")
async def get_assistant(assistant_id: str):
    if assistant_id == "visa_agent":
        return {
            "assistant_id": "visa_agent",
            "graph_id": "visa_agent", 
            "config": {},
            "metadata": {"type": "agent_based"}
        }
    raise HTTPException(status_code=404, detail="Assistant not found")

@app.post("/threads", response_model=ThreadResponse)
async def create_thread():
    thread_id = str(uuid.uuid4())
    # Initialize thread state
    thread_states[thread_id] = {
        "messages": [],
        "session_id": thread_id,
        "tool_call_count": 0,
        "state_version": 1
    }
    return ThreadResponse(thread_id=thread_id)

@app.post("/threads/{thread_id}/runs/wait", response_model=RunResponse)
async def run_thread(thread_id: str, request: MessageRequest):
    try:
        # Get the latest user message
        user_message = request.messages[-1]["content"]
        
        # Get current thread state or create new one
        if thread_id not in thread_states:
            thread_states[thread_id] = {
                "messages": [],
                "session_id": thread_id,
                "tool_call_count": 0,
                "state_version": 1
            }
        
        current_state = thread_states[thread_id]
        
        # Add user message to state
        user_msg = HumanMessage(content=user_message)
        current_state["messages"].append(user_msg)
        
        # Prepare input for agent
        agent_input = {
            "messages": current_state["messages"],
            "session_id": thread_id,
            "tool_call_count": current_state.get("tool_call_count", 0),
            "state_version": current_state.get("state_version", 1)
        }
        
        # Add any existing state fields
        for key, value in current_state.items():
            if key not in ["messages", "session_id", "tool_call_count", "state_version"] and value is not None:
                agent_input[key] = value
        
        # Run the agent
        result = invoke_agent(agent_input)
        
        # Update thread state with result
        thread_states[thread_id].update(result)
        
        # Extract response messages - handle both message objects and direct responses
        response_messages = []
        
        # Debug: Print what we got from agent
        print(f"Agent result keys: {result.keys()}")
        if "messages" in result:
            print(f"Messages type: {type(result['messages'])}")
            if result["messages"]:
                print(f"First message type: {type(result['messages'][-1])}")
        
        if "messages" in result and result["messages"]:
            # Get the last AI message
            for msg in reversed(result["messages"]):
                if hasattr(msg, 'type') and msg.type == 'ai':
                    # Extract clean text content from potentially complex message structure
                    content = _extract_clean_content(msg.content)
                    response_messages.append({
                        "role": "assistant", 
                        "content": content
                    })
                    break  # Only take the latest AI response
        
        # If no messages in result, check for direct response
        elif "response" in result:
            content = _extract_clean_content(result["response"])
            response_messages.append({
                "role": "assistant",
                "content": content
            })
        
        # Fallback: If no proper response found, provide error message
        if not response_messages:
            response_messages.append({
                "role": "assistant",
                "content": "I processed your request but couldn't generate a proper response. Please try again."
            })
        
        return RunResponse(messages=response_messages)
        
    except Exception as e:
        print(f"❌ Error in run_thread: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/threads/{thread_id}/state")
async def get_thread_state(thread_id: str):
    try:
        if thread_id in thread_states:
            # Return clean state without internal message objects
            state = thread_states[thread_id].copy()
            # Convert messages to serializable format
            if "messages" in state:
                serializable_messages = []
                for msg in state["messages"]:
                    if hasattr(msg, 'type') and hasattr(msg, 'content'):
                        serializable_messages.append({
                            "type": msg.type,
                            "content": msg.content
                        })
                state["messages"] = serializable_messages
            return {"state": state}
        else:
            return {"state": {}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Streaming endpoint that LangGraph React SDK expects
@app.post("/threads/{thread_id}/runs/stream")
async def stream_run(thread_id: str, request: dict):
    from fastapi.responses import StreamingResponse
    
    try:
        # Get the input messages
        input_data = request.get("input", {})
        messages = input_data.get("messages", [])
        
        if not messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        user_message = messages[-1]["content"]
        
        # Get current thread state or create new one
        if thread_id not in thread_states:
            thread_states[thread_id] = {
                "messages": [],
                "session_id": thread_id,
                "tool_call_count": 0,
                "state_version": 1
            }
        
        current_state = thread_states[thread_id]
        
        # Add user message to state
        user_msg = HumanMessage(content=user_message)
        current_state["messages"].append(user_msg)
        
        async def generate_stream():
            print(f"Starting agent stream for thread {thread_id}, message: {user_message}")
            
            # First, yield the user message in LangGraph format
            user_message_obj = {
                "id": f"user_{thread_id}",
                "type": "human", 
                "content": user_message,
                "created_at": "2025-01-01T00:00:00Z"
            }
            yield f"data: {json.dumps(user_message_obj)}\n\n"
            
            # Prepare input for agent streaming
            agent_input = {
                "messages": current_state["messages"],
                "session_id": thread_id,
                "tool_call_count": current_state.get("tool_call_count", 0),
                "state_version": current_state.get("state_version", 1)
            }
            
            # Add any existing state fields
            for key, value in current_state.items():
                if key not in ["messages", "session_id", "tool_call_count", "state_version"] and value is not None:
                    agent_input[key] = value
            
            # Stream the AI response using agent streaming
            try:
                async for chunk in stream_agent(agent_input):
                    if chunk and chunk.get("type") == "token":
                        ai_message_obj = {
                            "id": f"ai_{thread_id}_{chunk.get('token', '')[:10]}",
                            "type": "ai", 
                            "content": chunk["token"],
                            "created_at": "2025-01-01T00:00:00Z"
                        }
                        yield f"data: {json.dumps(ai_message_obj)}\n\n"
                        
            except Exception as stream_error:
                print(f"Streaming error: {stream_error}")
                error_message = {
                    "id": f"error_{thread_id}",
                    "type": "ai",
                    "content": "I encountered an issue processing your request. Please try again.",
                    "created_at": "2025-01-01T00:00:00Z"
                }
                yield f"data: {json.dumps(error_message)}\n\n"
            
            print("Agent stream completed")
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )
        
    except Exception as e:
        print(f"Error in stream_run: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# For local development
if __name__ == "__main__":
    import uvicorn
    import asyncio
    import sys
    
    # Fix for Windows asyncio event loop issue
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting Agent-based Visa Assistant on port {port}")
    
    # Enable auto-reload in development mode
    is_development = os.environ.get("ENVIRONMENT", "development") == "development"
    
    if is_development:
        print("Development mode: Auto-reload enabled")
        uvicorn.run(
            "production_app:app",  # Import string format required for reload
            host="0.0.0.0", 
            port=port,
            reload=True,
            reload_dirs=["./"]
        )
    else:
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=port
        )