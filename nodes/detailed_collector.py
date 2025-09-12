from state import State
from langchain_core.messages import AIMessage
import json

def detailed_collector(state: State) -> dict:
    initial_info = state.get("initial_info", {})
    
    # print("DEBUG: I'm in next node (detailed_collector)")
    # print(f"Collected initial_info: {json.dumps(initial_info, indent=2)}")
    
    message = f"""Here's what I collected from the initial information gathering:

**Country**: {initial_info.get('country', 'Not specified')}
**Purpose of Travel**: {initial_info.get('purpose_of_travel', 'Not specified')}
**Number of Travelers**: {initial_info.get('number_of_travelers', 'Not specified')}  
**Travel Dates**: {initial_info.get('travel_dates', 'Not specified')}

Could you please upload the passport of {initial_info.get('number_of_travelers', 1)} traveler(s) and provide hotel booking details if any?
"""
    
    return {"messages": [AIMessage(content=message)]}