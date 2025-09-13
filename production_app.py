from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import uuid
from graph.builder import build_graph

# Global connection pool
connection_pool = None
checkpointer = None
compiled_graph = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global connection_pool, checkpointer, compiled_graph
    
    # Startup - Initialize PostgreSQL checkpointer
    database_uri = os.getenv("DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/langgraph")
    
    # For local testing, skip PostgreSQL and use memory checkpointer
    if os.getenv("ENVIRONMENT") == "production":
        try:
            connection_pool = AsyncConnectionPool(conninfo=database_uri)
            checkpointer = AsyncPostgresSaver(connection_pool)
            await checkpointer.setup()
            
            # Build graph with PostgreSQL checkpointer
            compiled_graph = build_graph(checkpointer=checkpointer)
            
            print("✅ LangGraph production server initialized with PostgreSQL")
            
        except Exception as e:
            print(f"❌ Failed to initialize PostgreSQL: {e}")
            raise e
    else:
        # Local development - use memory checkpointer
        from langgraph.checkpoint.memory import MemorySaver
        checkpointer = MemorySaver()
        compiled_graph = build_graph(checkpointer=checkpointer)
        print("⚠️ Using memory checkpointer for local development")
    
    yield
    
    # Shutdown
    if connection_pool:
        await connection_pool.close()

app = FastAPI(
    title="Visa Agent API",
    description="Production LangGraph Visa Agent",
    version="1.0.0",
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
    return {"status": "healthy", "service": "visa-agent"}

# LangGraph React SDK compatible endpoints
@app.get("/assistants/{assistant_id}")
async def get_assistant(assistant_id: str):
    if assistant_id == "visa_agent":
        return {
            "assistant_id": "visa_agent",
            "graph_id": "visa_agent", 
            "config": {},
            "metadata": {}
        }
    raise HTTPException(status_code=404, detail="Assistant not found")

@app.post("/threads", response_model=ThreadResponse)
async def create_thread():
    thread_id = str(uuid.uuid4())
    return ThreadResponse(thread_id=thread_id)

# Store message counts per thread to track new messages
thread_message_counts = {}

@app.post("/threads/{thread_id}/runs/wait", response_model=RunResponse)
async def run_thread(thread_id: str, request: MessageRequest):
    if not compiled_graph:
        raise HTTPException(status_code=500, detail="Graph not initialized")
    
    try:
        # Get the latest user message
        user_message = request.messages[-1]["content"]
        
        # Configuration with thread_id for checkpointing
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        # Get current message count before running
        current_state = await compiled_graph.aget_state(config)
        messages_before = 0
        if current_state and current_state.values and "messages" in current_state.values:
            messages_before = len(current_state.values["messages"])
        
        # Run the graph with persistent state
        result = await compiled_graph.ainvoke(
            {"messages": [{"role": "human", "content": user_message}]},
            config=config
        )
        
        # Get messages after running
        new_state = await compiled_graph.aget_state(config)
        response_messages = []
        
        if new_state and new_state.values and "messages" in new_state.values:
            all_messages = new_state.values["messages"]
            # Get only the NEW AI messages (after the previous count)
            new_messages = all_messages[messages_before:]
            
            for msg in new_messages:
                if hasattr(msg, 'content') and hasattr(msg, 'type'):
                    if msg.type == 'ai':  # Include ALL new AI messages
                        response_messages.append({
                            "role": "assistant", 
                            "content": msg.content
                        })
        
        return RunResponse(messages=response_messages)
        
    except Exception as e:
        print(f"❌ Error in run_thread: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/threads/{thread_id}/state")
async def get_thread_state(thread_id: str):
    if not compiled_graph:
        raise HTTPException(status_code=500, detail="Graph not initialized")
    
    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = await compiled_graph.aget_state(config)
        return {"state": state.values if state else {}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Streaming endpoint that LangGraph React SDK expects
@app.post("/threads/{thread_id}/runs/stream")
async def stream_run(thread_id: str, request: dict):
    from fastapi.responses import StreamingResponse
    import json
    
    try:
        # Get the input messages
        input_data = request.get("input", {})
        messages = input_data.get("messages", [])
        
        if not messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        user_message = messages[-1]["content"]
        
        # Configuration with thread_id for checkpointing
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        async def generate_stream():
            print(f"Starting stream for thread {thread_id}, message: {user_message}")
            
            # First, yield the user message in LangGraph format
            user_message_obj = {
                "id": f"user_{thread_id}",
                "type": "human", 
                "content": user_message,
                "created_at": "2025-01-01T00:00:00Z"
            }
            yield f"data: {json.dumps(user_message_obj)}\n\n"
            
            # Stream the AI response
            async for chunk in compiled_graph.astream(
                {"messages": [{"role": "human", "content": user_message}]},
                config=config
            ):
                print(f"Stream chunk: {chunk}")
                # Look for messages in the chunk values
                for node_name, node_data in chunk.items():
                    if node_data and isinstance(node_data, dict) and "messages" in node_data:
                        print(f"Found messages in {node_name}: {node_data['messages']}")
                        for msg in node_data["messages"]:
                            if hasattr(msg, 'content') and hasattr(msg, 'type'):
                                print(f"Message type: {msg.type}, content: {msg.content}")
                                if msg.type == 'ai':
                                    ai_message_obj = {
                                        "id": f"ai_{thread_id}_{msg.id}",
                                        "type": "ai", 
                                        "content": msg.content,
                                        "created_at": "2025-01-01T00:00:00Z"
                                    }
                                    print(f"Yielding AI message: {msg.content}")
                                    yield f"data: {json.dumps(ai_message_obj)}\n\n"
            
            print("Stream completed")
        
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

# Temporarily disabled debug endpoint
# @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
# async def catch_all(path: str, request: Request):
#     print(f"Missing endpoint: {request.method} /{path}")
#     raise HTTPException(status_code=404, detail=f"Endpoint not found: {request.method} /{path}")

# For local development
if __name__ == "__main__":
    import uvicorn
    import asyncio
    import sys
    
    # Fix for Windows asyncio event loop issue with psycopg
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)