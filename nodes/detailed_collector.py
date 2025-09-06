from state import State
import json

def detailed_collector(state: State) -> dict:
    initial_info = state.get("initial_info", {})
    
    # print("DEBUG: I'm in next node (detailed_collector)")
    # print(f"Collected initial_info: {json.dumps(initial_info, indent=2)}")
    
    message = f"""Here's what I collected from the initial information gathering:

**Country**: {initial_info.get('country', 'Not specified')}
**Travelers**: {initial_info.get('travelers', 'Not specified')}  
**Visa Type**: {initial_info.get('visa_type', 'Not specified')}

Could you please upload the passport of {initial_info.get('travelers', 1)} traveler(s) and provide hotel booking details if any?
"""
    
    return {"messages": message}