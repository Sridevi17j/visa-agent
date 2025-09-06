from state import State
from config.settings import llm
from utils.prompts import system_prompt, IntentClassification
from langchain_core.messages import HumanMessage, AIMessage

def intent_analyser(state:State) -> dict:
    user_message = state["messages"][-1].content
    
    # Handle empty or whitespace-only messages - just respond and wait for next input
    if not user_message or not user_message.strip():
        return {
            "messages": [AIMessage(content="Hey, you haven't entered anything! Please provide your question or let me know how I can help you with your visa needs.")]
        }
    
    # If we're awaiting user response for visa collection, route back to collector
    if state.get("awaiting_user_response"):
        return {"next": "base_information_collector"}
    
    if state.get("incomplete_session_id") and user_message.lower().strip() in ["yes", "y", "no", "n", "continue", "proceed", "start over"]:
        return {"next": "handle_resume_decision"}
    
    try:
        # Use structured output with your detailed prompt
        structured_llm = llm.with_structured_output(IntentClassification)
        result = structured_llm.invoke([system_prompt, HumanMessage(content=user_message)])
        
        # Route based on classified intent
        if result.user_intent == "greetings":
            return {"next": "greetings"}
        elif result.user_intent == "general_enquiry":
            return {"next": "general_enquiry"}
        elif result.user_intent == "document_submission":
            return {"next": "docs_parser"}
        else:  # visa_application
            return {"next": "visa_application"}
            
    except Exception as e:
        print(f"Intent classification error: {e}")
        # Safe fallback to general enquiry
        return {"next": "general_enquiry"}
