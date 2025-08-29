from state import State
from utils.file_manager import load_incomplete_application, delete_incomplete_application

def collection_resume(state: State) -> dict:
    
    session_id = state.get("incomplete_session_id")
    
    if not session_id:
        return {
            "messages": "No incomplete application found. Let's start fresh!",
            "next": "visa_application_collector"
        }
    
    missing_fields = state.get("missing_fields", [])
    missing_labels = {
        "destination": "country",
        "num_travelers": "number of travelers", 
        "visa_type": "visa type"
    }
    
    missing_items = [missing_labels.get(field, field) for field in missing_fields]
    missing_text = ", ".join(missing_items)
    
    message = f"I answered your question! Would you like to continue with your visa application? "
    message += f"I still need: {missing_text}."
    message += f"\n\nType 'yes' to continue or 'no' to start over."
    
    return {
        "messages": message,
        "next": "wait_for_resume_decision"
    }

def handle_resume_decision(state: State) -> dict:
    
    user_response = state["messages"][-1].content.lower().strip()
    session_id = state.get("incomplete_session_id")
    
    if user_response in ["yes", "y", "continue", "proceed"]:
        if session_id:
            incomplete_data = load_incomplete_application(session_id)
            
            if incomplete_data:
                collected_data = incomplete_data.get("collected_data", {})
                updates = {
                    "collection_in_progress": True,
                    "missing_fields": incomplete_data.get("missing_fields", []),
                    "next": "visa_application_collector"
                }
                
                for key, value in collected_data.items():
                    if value:
                        updates[key] = value
                
                delete_incomplete_application(session_id)
                
                return updates
        
        return {
            "messages": "Let's continue with your visa application.",
            "collection_in_progress": True,
            "next": "visa_application_collector"
        }
    
    else:
        if session_id:
            delete_incomplete_application(session_id)
        
        return {
            "messages": "No problem! Let's start fresh with your visa application.",
            "collection_in_progress": False,
            "incomplete_session_id": None,
            "missing_fields": None,
            "next": "visa_application_collector"
        }
