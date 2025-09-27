# Main application entry point for agent-based visa assistant
# Purpose: Simple terminal interface for testing with streaming

import sys
import os
import asyncio
# Add current directory to Python path so agent_based_assistant/ becomes the import root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.agent import stream_agent
from langchain_core.messages import HumanMessage


async def main():
    """Simple terminal interface for testing the visa agent"""
    
    print("Type 'quit' to exit\n")
    
    # Initialize state
    state = {
        "messages": [],
        "tool_call_count": 0,
        "state_version": 1
    }
    
    while True:
        try:
            user_input = input("\nUser: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
                
            if not user_input:
                continue
            
            # Add user message
            state["messages"].append(HumanMessage(content=user_input))
            
            # Stream agent response with token-level streaming
            print("Agent: ", end="", flush=True)
            full_response = ""
            
            async for chunk in stream_agent(state):
                if chunk is None:
                    continue  # Skip None chunks (filtered out chunks)
                    
                if chunk.get("type") == "token":
                    # Real-time token streaming (following LangGraph docs pattern)
                    token_text = chunk["token"]
                    print(token_text, end="", flush=True)
                    full_response += token_text
            
            # Add newline after streaming and update state
            print()  # New line after streaming
            if full_response:
                # Add the complete response to our state messages
                from langchain_core.messages import AIMessage
                state["messages"].append(AIMessage(content=full_response))
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())