from state import State
from config.settings import llm
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field
from typing import Optional

class VisaInfo(BaseModel):
    country: Optional[str] = Field(None, description="Country name (capitalized)")
    purpose_of_travel: Optional[str] = Field(None, description="Purpose of travel (e.g., tourism, business, work, study, transit)")

def base_information_collector(state: State) -> dict:
    current_initial_info = state.get("initial_info", {})
    
    # Get the latest USER message (filter by message type)
    user_message = ""
    for msg in reversed(state["messages"]):
        if hasattr(msg, 'type') and msg.type == 'human':
            user_message = msg.content
            break
    
    # Handle empty or whitespace-only messages
    if not user_message or not user_message.strip():
        return {
            "messages": [AIMessage(content="I didn't receive your response. Please provide the information I asked for.")],
            "awaiting_user_response": True
        }
    
    # print(f"DEBUG: User message: {user_message}")
    # print(f"DEBUG: Current initial_info: {current_initial_info}")
    # print(f"DEBUG: All messages in state:")
    # for i, msg in enumerate(state["messages"]):
    #     msg_type = getattr(msg, 'type', 'unknown')
    #     msg_role = msg.get('role', 'no_role') if isinstance(msg, dict) else 'not_dict'
    #     msg_content = getattr(msg, 'content', str(msg)[:50])
    #     print(f"  [{i}] Type: {msg_type}, Role: {msg_role}, Content: {msg_content}")
    # print("DEBUG: ---")
    
    # Use structured output method (modern LangGraph best practice)
    structured_llm = llm.with_structured_output(VisaInfo)
    
    extraction_prompt = f"""
    Extract visa information from this user message: "{user_message}"
    
    Current information we already have: {current_initial_info}
    
    STRICT EXTRACTION RULES - Only extract if EXPLICITLY mentioned:
    - country: Only if a specific country name is mentioned
    - purpose_of_travel: Only if user explicitly mentions purpose (tourism, business, work, study, transit, etc.)
    
    DO NOT assume or guess. Set fields to null if not explicitly mentioned.
    """
    
    try:
        extracted_data = structured_llm.invoke([HumanMessage(content=extraction_prompt)])
        
        # print(f"DEBUG: LLM structured output: {extracted_data}")
        
        # Merge with current info
        extracted_info = current_initial_info.copy()
        if extracted_data.country:
            extracted_info["country"] = extracted_data.country
        if extracted_data.purpose_of_travel:
            extracted_info["purpose_of_travel"] = extracted_data.purpose_of_travel
        
        # Reset retry counter on successful extraction
        return_data = {"extraction_retry_count": 0}
            
    except Exception as e:
        # print(f"DEBUG: Structured extraction failed: {e}")
        
        # Check retry count to prevent infinite loops
        retry_count = state.get("extraction_retry_count", 0)
        
        if retry_count >= 1:
            # Max retries reached, give up gracefully
            return {
                "messages": [AIMessage(content="I'm having difficulty processing your request. Please try again later.")],
                "extraction_retry_count": 0  # Reset for next session
            }
        else:
            # First failure, ask user to retry with all information
            return {
                "messages": [AIMessage(content="Sorry, I had an issue. Which country do you want to visit and what is your purpose of travel?")],
                "extraction_retry_count": retry_count + 1,
                "initial_info": {},  # Reset for fresh start
                "awaiting_user_response": True
            }
    else:
        # Only set return_data if no exception occurred
        return_data = {"extraction_retry_count": 0}
    
    # print(f"DEBUG: Final extracted info: {extracted_info}")
    
    # Check what's still missing
    missing_fields = []
    if not extracted_info.get("country"):
        missing_fields.append("country")
    if not extracted_info.get("purpose_of_travel"):
        missing_fields.append("purpose_of_travel")
    
    # If all information is collected, proceed to next node
    if not missing_fields:
        result = {
            "messages": [AIMessage(content=f"Perfect! I have all the required information:\n- Country: {extracted_info['country']}\n- Purpose of Travel: {extracted_info['purpose_of_travel']}\n\nLet me proceed to collect detailed information.")],
            "initial_info": extracted_info,
            "awaiting_user_response": False,
            "next": "detailed_collector"
        }
        result.update(return_data)  # Include retry counter reset
        return result
    
    # Ask for all missing information in one message
    question_parts = []
    if "country" in missing_fields:
        question_parts.append("Which country are you visiting?")
    if "purpose_of_travel" in missing_fields:
        question_parts.append("What is your purpose of travel? (e.g., tourism, business, work, study, transit)")
    
    question = "I need a few more details:\n\n" + "\n".join([f"{i+1}. {q}" for i, q in enumerate(question_parts)])
    question += "\n\nPlease provide all the missing information in your response."
    
    result = {
        "messages": [AIMessage(content=question)],
        "initial_info": extracted_info,
        "awaiting_user_response": True
    }
    result.update(return_data)  # Include retry counter reset
    return result
