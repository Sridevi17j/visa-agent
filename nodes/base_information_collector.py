from state import State
from config.settings import llm
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field
from typing import Optional

class VisaInfo(BaseModel):
    country: Optional[str] = Field(None, description="Country name (capitalized)")
    purpose_of_travel: Optional[str] = Field(None, description="Purpose of travel (e.g., tourism, business, work, study, transit)")
    number_of_travelers: Optional[int] = Field(None, description="Number of travelers as integer. Extract from phrases like '2 people', 'three persons', 'solo trip' (=1), 'me and my wife' (=2), 'family of 4' (=4)")
    travel_dates: Optional[str] = Field(None, description="Travel dates from and to in DD/MM/YY format. Convert any input to this standard format: '24 Jan to 3rd Feb 2026' → '24/01/26 to 03/02/26', 'January 24 to February 2, 2026' → '24/01/26 to 02/02/26'. If cannot convert (like 'next month'), keep original.")

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
    
    # CASE 1: Direct answer - user answered our specific question
    if state.get("user_answer_category") == "answer":
        return handle_direct_answer(user_message, current_initial_info, state)
    
    # CASE 2: Restored state from collection_resume (returning from general enquiry)
    elif state.get("collection_in_progress") and not state.get("user_answer_category"):
        return handle_restored_collection(current_initial_info, state)
    
    # CASE 3: Initial collection (first time from visa_application or fresh start)
    else:
        return handle_initial_collection(user_message, current_initial_info, state)
    
def handle_direct_answer(user_message: str, current_initial_info: dict, state: State) -> dict:
    """Handle when user directly answered our question (user_answer_category='answer')"""
    return extract_and_process_info(user_message, current_initial_info, state)

def handle_restored_collection(current_initial_info: dict, state: State) -> dict:
    """Handle returning from general_enquiry context switch"""
    # Clear temporary flags
    result = {
        "collection_in_progress": False,
        "user_answer_category": None,
    }
    
    # Check what's still missing and ask for it
    missing_fields = []
    if not current_initial_info.get("country"):
        missing_fields.append("country")
    if not current_initial_info.get("purpose_of_travel"):
        missing_fields.append("purpose_of_travel")
    if not current_initial_info.get("number_of_travelers"):
        missing_fields.append("number_of_travelers")
    if not current_initial_info.get("travel_dates"):
        missing_fields.append("travel_dates")
    
    if not missing_fields:
        # All info collected, proceed
        result.update({
            "messages": [AIMessage(content=f"Perfect! I have all the required information:\n- Country: {current_initial_info['country']}\n- Purpose of Travel: {current_initial_info['purpose_of_travel']}\n- Number of Travelers: {current_initial_info['number_of_travelers']}\n- Travel Dates: {current_initial_info['travel_dates']}\n\nLet me proceed to collect detailed information.")],
            "initial_info": current_initial_info,
            "awaiting_user_response": False,
            "next": "detailed_collector"
        })
    else:
        # Ask for missing fields
        question_parts = []
        if "country" in missing_fields:
            question_parts.append("Which country are you visiting?")
        if "purpose_of_travel" in missing_fields:
            question_parts.append("What is your purpose of travel? (e.g., tourism, business, work, study, transit)")
        if "number_of_travelers" in missing_fields:
            question_parts.append("How many travelers? (e.g., 1, 2, 3)")
        if "travel_dates" in missing_fields:
            question_parts.append("What are your travel dates? (e.g., '24/01/26 to 02/02/26', '24 Jan to 2 Feb 2026')")
        
        question = "Let's continue with your visa application. " + "\n".join([f"{i+1}. {q}" for i, q in enumerate(question_parts)])
        question += "\n\nPlease provide the missing information."
        
        result.update({
            "messages": [AIMessage(content=question)],
            "initial_info": current_initial_info,
            "awaiting_user_response": True
        })
    
    return result

def handle_initial_collection(user_message: str, current_initial_info: dict, state: State) -> dict:
    """Handle first time entry from visa_application or fresh start"""
    return extract_and_process_info(user_message, current_initial_info, state)

def extract_and_process_info(user_message: str, current_initial_info: dict, state: State) -> dict:
    """Core extraction and processing logic"""
    # Use structured output method (modern LangGraph best practice)
    structured_llm = llm.with_structured_output(VisaInfo)
    
    extraction_prompt = f"""
    Extract visa information from this user message: "{user_message}"
    
    Current information we already have: {current_initial_info}
    
    STRICT EXTRACTION RULES - Only extract if EXPLICITLY mentioned:
    - country: Only if a specific country name is mentioned
    - purpose_of_travel: Only if user explicitly mentions purpose (tourism, business, work, study, transit, etc.)
    - number_of_travelers: Convert to integer from phrases like "2 people", "three travelers", "solo trip" (=1), "me and my wife" (=2), "family of 4" (=4)
    - travel_dates: Travel dates from and to. Extract from formats like "24/01/26 to 02/02/26", "24 Jan to 2 Feb 2026", "from 15th March to 28th March", "next month", "in 2 weeks"
    
    DO NOT assume or guess. Set fields to null if not explicitly mentioned.
    """
    
    try:
        extracted_data = structured_llm.invoke([HumanMessage(content=extraction_prompt)])
        
        # Merge with current info
        extracted_info = current_initial_info.copy()
        if extracted_data.country:
            extracted_info["country"] = extracted_data.country
        if extracted_data.purpose_of_travel:
            extracted_info["purpose_of_travel"] = extracted_data.purpose_of_travel
        if extracted_data.number_of_travelers:
            extracted_info["number_of_travelers"] = extracted_data.number_of_travelers
        if extracted_data.travel_dates:
            extracted_info["travel_dates"] = extracted_data.travel_dates
        
        # Reset retry counter on successful extraction
        return_data = {"extraction_retry_count": 0, "user_answer_category": None}
            
    except Exception as e:
        # Check retry count to prevent infinite loops
        retry_count = state.get("extraction_retry_count", 0)
        
        if retry_count >= 1:
            # Max retries reached, give up gracefully
            return {
                "messages": [AIMessage(content="I'm having difficulty processing your request. Please try again later.")],
                "extraction_retry_count": 0,
                "user_answer_category": None
            }
        else:
            # First failure, ask user to retry with all information
            return {
                "messages": [AIMessage(content="Sorry, I had an issue. Which country do you want to visit and what is your purpose of travel?")],
                "extraction_retry_count": retry_count + 1,
                "initial_info": {},
                "awaiting_user_response": True,
                "user_answer_category": None
            }
    else:
        # Only set return_data if no exception occurred
        return_data = {"extraction_retry_count": 0, "user_answer_category": None}
    
    # Check what's still missing
    missing_fields = []
    if not extracted_info.get("country"):
        missing_fields.append("country")
    if not extracted_info.get("purpose_of_travel"):
        missing_fields.append("purpose_of_travel")
    if not extracted_info.get("number_of_travelers"):
        missing_fields.append("number_of_travelers")
    if not extracted_info.get("travel_dates"):
        missing_fields.append("travel_dates")
    
    # If all information is collected, proceed to next node
    if not missing_fields:
        result = {
            "messages": [AIMessage(content=f"Perfect! I have all the required information:\n- Country: {extracted_info['country']}\n- Purpose of Travel: {extracted_info['purpose_of_travel']}\n- Number of Travelers: {extracted_info['number_of_travelers']}\n- Travel Dates: {extracted_info['travel_dates']}\n\nLet me proceed to collect detailed information.")],
            "initial_info": extracted_info,
            "awaiting_user_response": False,
            "next": "detailed_collector"
        }
        result.update(return_data)
        return result
    
    # Ask for all missing information in one message
    question_parts = []
    if "country" in missing_fields:
        question_parts.append("Which country are you visiting?")
    if "purpose_of_travel" in missing_fields:
        question_parts.append("What is your purpose of travel? (e.g., tourism, business, work, study, transit)")
    if "number_of_travelers" in missing_fields:
        question_parts.append("How many travelers? (e.g., 1, 2, 3)")
    if "travel_dates" in missing_fields:
        question_parts.append("What are your travel dates? (e.g., '24/01/26 to 02/02/26', '24 Jan to 2 Feb 2026')")
    
    question = "I need a few more details:\n\n" + "\n".join([f"{i+1}. {q}" for i, q in enumerate(question_parts)])
    question += "\n\nPlease provide all the missing information in your response."
    
    result = {
        "messages": [AIMessage(content=question)],
        "initial_info": extracted_info,
        "awaiting_user_response": True
    }
    result.update(return_data)
    return result
