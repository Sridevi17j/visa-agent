from state import State
from config.settings import llm
from utils.prompts import system_prompt, IntentClassification
from langchain_core.messages import HumanMessage, AIMessage

def classify_user_response(assistant_question: str, user_message: str) -> str:
    """Use LLM to determine if user is answering our question or asking something else"""
    try:
        classification_prompt = f"""
        CONTEXT: I asked the user this question: "{assistant_question}"
        
        USER'S RESPONSE: "{user_message}"
        
        TASK: Determine if the user is answering my question or asking something else entirely.
        
        EXAMPLES:
        - If I asked "What is your purpose of travel?" and user says "tourism" → ANSWER
        - If I asked "What is your purpose of travel?" and user says "what are land borders?" → GENERAL_ENQUIRY
        - If I asked "Which country?" and user says "Vietnam" → ANSWER  
        - If I asked "Which country?" and user says "tell me visa requirements" → GENERAL_ENQUIRY
        
        Respond with only: "answer" or "general_enquiry"
        """
        
        response = llm.invoke([HumanMessage(content=classification_prompt)])
        result = response.content.strip().lower()
        
        if "answer" in result:
            return "answer"
        elif "general_enquiry" in result or "general" in result:
            return "general_enquiry"
        else:
            return "answer"  # Default fallback
            
    except Exception as e:
        print(f"Error in classify_user_response: {e}")
        return "answer"  # Safe fallback

def intent_analyser(state:State) -> dict:
    user_message = state["messages"][-1].content
    
    # Handle empty or whitespace-only messages - just respond and wait for next input
    if not user_message or not user_message.strip():
        return {
            "messages": [AIMessage(content="Hey, you haven't entered anything! Please provide your question or let me know how I can help you with your visa needs.")]
        }
    
    # If we're awaiting user response, analyze if user is answering or asking something else
    if state.get("awaiting_user_response"):
        try:
            # Get the last assistant message (our pending question)
            assistant_question = ""
            for msg in reversed(state["messages"][:-1]):  # Exclude current user message
                if hasattr(msg, 'type') and msg.type == 'ai':
                    assistant_question = msg.content
                    break
            
            # LLM determines if user is answering our question or asking something else
            user_answer_category = classify_user_response(assistant_question, user_message)
            
            if user_answer_category == "answer":
                return {
                    "next": "base_information_collector", 
                    "user_answer_category": "answer"
                }
            elif user_answer_category == "general_enquiry":
                return {
                    "next": "general_enquiry",
                    "user_answer_category": "general_enquiry", 
                    "collection_in_progress": True,
                    "incomplete_initial_info": state.get("initial_info", {}),
                    "previous_node": "base_information_collector"
                }
            else:
                # Fallback to base_information_collector for unclear cases
                return {"next": "base_information_collector", "user_answer_category": "answer"}
                
        except Exception as e:
            print(f"Context switching analysis error: {e}")
            # Fallback to continuing collection
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
