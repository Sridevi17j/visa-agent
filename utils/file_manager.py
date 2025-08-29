import json
import os
import uuid
from datetime import datetime
from state import State

def save_incomplete_application(state: State) -> str:
    session_id = str(uuid.uuid4())[:8]
    
    incomplete_data = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "collected_data": {
            "travel_details": state.get("travel_details", []),
            "visa_details": state.get("visa_details", []),
            "personal_info": state.get("personal_info", []),
            "passport_info": state.get("passport_info", []),
            "employment_info": state.get("employment_info", []),
            "financial_info": state.get("financial_info", []),
            "accommodation_info": state.get("accommodation_info", []),
            "document_uploads": state.get("document_uploads", []),
            "emergency_contacts": state.get("emergency_contacts", []),
            "insurance_info": state.get("insurance_info", [])
        },
        "missing_fields": state.get("missing_fields", [])
    }
    
    os.makedirs("incomplete_applications", exist_ok=True)
    
    filename = f"incomplete_applications/session_{session_id}.json"
    with open(filename, 'w') as f:
        json.dump(incomplete_data, f, indent=2)
    
    return session_id

def load_incomplete_application(session_id: str) -> dict:
    filename = f"incomplete_applications/session_{session_id}.json"
    
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}

def delete_incomplete_application(session_id: str):
    filename = f"incomplete_applications/session_{session_id}.json"
    if os.path.exists(filename):
        os.remove(filename)
