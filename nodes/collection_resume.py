from state import State
from config.settings import llm
from langchain_core.messages import HumanMessage, AIMessage
from utils.file_manager import load_incomplete_application, delete_incomplete_application

def collection_resume(state: State) -> dict:
    # Handle new context switching flow (from general_enquiry)
    if state.get("collection_in_progress") and state.get("incomplete_initial_info"):
        incomplete_info = state.get("incomplete_initial_info", {})
        
        # Determine what fields are still missing
        missing_fields = []
        if not incomplete_info.get("country"):
            missing_fields.append("country")
        if not incomplete_info.get("purpose_of_travel"):
            missing_fields.append("purpose_of_travel")
        if not incomplete_info.get("number_of_travelers"):
            missing_fields.append("number_of_travelers")
        if not incomplete_info.get("travel_dates"):
            missing_fields.append("travel_dates")
        
        missing_labels = {
            "country": "country",
            "purpose_of_travel": "purpose of travel",
            "number_of_travelers": "number of travelers",
            "travel_dates": "travel dates"
        }
        
        missing_items = [missing_labels.get(field, field) for field in missing_fields]
        missing_text = ", ".join(missing_items) if missing_items else "nothing more"
        
        # Preserve the previous message (general_enquiry answer) and append continuation
        previous_messages = state.get("messages", [])
        
        continuation_message = f"I answered your question! Would you like to continue with your visa application? "
        if missing_items:
            continuation_message += f"I still need: {missing_text}."
        else:
            continuation_message += "I have all the basic information."
        continuation_message += f"\n\nType 'yes' to continue or 'no' to quit."
        
        return {
            "messages": previous_messages + [AIMessage(content=continuation_message)],
            "next": "handle_resume_decision"
        }
    
    # Legacy flow with incomplete_session_id
    session_id = state.get("incomplete_session_id")
    
    if not session_id:
        return {
            "messages": "No incomplete application found. Let's start fresh!",
            "next": "base_information_collector"
        }
    
    missing_fields = state.get("missing_fields", [])
    missing_labels = {
        "country": "country",
        "purpose_of_travel": "purpose of travel",
        "number_of_travelers": "number of travelers",
        "travel_dates": "travel dates"
    }
    
    missing_items = [missing_labels.get(field, field) for field in missing_fields]
    missing_text = ", ".join(missing_items)
    
    message = f"I answered your question! Would you like to continue with your visa application? "
    message += f"I still need: {missing_text}."
    message += f"\n\nType 'yes' to continue or 'no' to start over."
    
    return {
        "messages": message,
        "next": "handle_resume_decision"
    }

def classify_resume_response(user_message: str, context: str) -> str:
    """Use LLM to classify user's intent regarding visa application resume"""
    try:
        classification_prompt = f"""
        CONTEXT: {context}
        USER RESPONSE: "{user_message}"
        
        Classify the user's intent into ONE category:
        
        1. RESUME - User wants to continue visa application
           Examples: "yes", "continue", "proceed", "let's go", "okay"
        
        2. DECLINE - User wants to quit/cancel visa application  
           Examples: "no", "cancel", "quit", "stop", "bye", "end", "I'm done"
        
        3. CONFIRMED_QUIT - User confirms they want to quit (after asking "are you sure?")
           Examples: "yes quit", "I'm sure", "definitely no", "yes cancel"
        
        4. WANT_TO_CONTINUE - User changed mind, wants to continue (after decline)
           Examples: "actually yes", "wait no", "let me continue", "I'll continue"
        
        5. UNCLEAR - Response is ambiguous or unclear
           Examples: "maybe", "hmm", "what?", random text
        
        Respond with only the category name.
        """
        
        response = llm.invoke([HumanMessage(content=classification_prompt)])
        return response.content.strip().upper()
    except Exception as e:
        print(f"Error in classify_resume_response: {e}")
        return "UNCLEAR"

def format_progress_summary(incomplete_info: dict) -> str:
    """Format user's progress for confirmation message"""
    parts = []
    if incomplete_info.get("country"):
        parts.append(f"Country: {incomplete_info['country']}")
    if incomplete_info.get("purpose_of_travel"):
        parts.append(f"Purpose: {incomplete_info['purpose_of_travel']}")
    if incomplete_info.get("number_of_travelers"):
        parts.append(f"Travelers: {incomplete_info['number_of_travelers']}")
    if incomplete_info.get("travel_dates"):
        parts.append(f"Dates: {incomplete_info['travel_dates']}")
    
    return ", ".join(parts) if parts else "some information collected"

def handle_resume_decision(state: State) -> dict:
    user_message = state["messages"][-1].content
    incomplete_info = state.get("incomplete_initial_info", {})
    confirmation_pending = state.get("confirmation_pending", False)
    session_id = state.get("incomplete_session_id")
    
    # Determine context for LLM
    if confirmation_pending:
        context = "I asked user to confirm if they want to quit their visa application"
    else:
        context = "I asked user if they want to continue their visa application"
    
    # Classify user response using LLM
    intent = classify_resume_response(user_message, context)
    
    if intent == "RESUME":
        return resume_visa_application(state)
    
    elif intent == "DECLINE" and not confirmation_pending:
        # First time decline - ask for confirmation
        progress_summary = format_progress_summary(incomplete_info)
        return {
            "messages": [AIMessage(content=f"Are you sure you want to quit your visa application? You'll lose your progress ({progress_summary}). Type 'yes' to quit or 'no' to continue.")],
            "confirmation_pending": True,
            "next": "handle_resume_decision"
        }
    
    elif intent == "CONFIRMED_QUIT" and confirmation_pending:
        return quit_visa_application()
    
    elif intent == "WANT_TO_CONTINUE" and confirmation_pending:
        return resume_visa_application(state)
    
    elif intent == "UNCLEAR":
        if confirmation_pending:
            return {
                "messages": [AIMessage(content="Please say 'yes' to quit your application or 'no' to continue with your visa.")],
                "next": "handle_resume_decision"
            }
        else:
            return {
                "messages": [AIMessage(content="Please say 'yes' to continue your visa application or 'no' to quit.")],
                "next": "handle_resume_decision"
            }
    
    else:
        # Fallback for any other cases
        if confirmation_pending:
            return {
                "messages": [AIMessage(content="Please say 'yes' to quit or 'no' to continue.")],
                "next": "handle_resume_decision"
            }
        else:
            return {
                "messages": [AIMessage(content="Please say 'yes' to continue or 'no' to quit.")],
                "next": "handle_resume_decision"
            }

def resume_visa_application(state: State) -> dict:
    """Resume the visa application with saved state"""
    # Handle context switching resume
    if state.get("incomplete_initial_info"):
        return {
            "messages": [AIMessage(content="Great! Let's continue with your visa application.")],
            "collection_in_progress": True,  # Will trigger restored_collection logic
            "initial_info": state.get("incomplete_initial_info", {}),
            "confirmation_pending": False,
            "user_answer_category": None,
            "next": "base_information_collector"
        }
    
    # Legacy session-based resume
    session_id = state.get("incomplete_session_id")
    if session_id:
        incomplete_data = load_incomplete_application(session_id)
        if incomplete_data:
            collected_data = incomplete_data.get("collected_data", {})
            updates = {
                "messages": [AIMessage(content="Great! Let's continue with your visa application.")],
                "collection_in_progress": True,
                "missing_fields": incomplete_data.get("missing_fields", []),
                "confirmation_pending": False,
                "next": "base_information_collector"
            }
            
            for key, value in collected_data.items():
                if value:
                    updates[key] = value
            
            delete_incomplete_application(session_id)
            return updates
    
    # Fallback
    return {
        "messages": [AIMessage(content="Let's continue with your visa application.")],
        "collection_in_progress": False,
        "confirmation_pending": False,
        "next": "base_information_collector"
    }

def quit_visa_application() -> dict:
    """Clear all state and start fresh"""
    return {
        "messages": [AIMessage(content="No problem! Your visa application has been cancelled. Feel free to start a new application or ask any visa-related questions.")],
        "awaiting_user_response": False,
        "initial_info": {},
        "collection_in_progress": False,
        "incomplete_initial_info": {},
        "confirmation_pending": False,
        "user_answer_category": None,
        "previous_node": None,
        "incomplete_session_id": None,
        "next": "intent_analyser"
    }
