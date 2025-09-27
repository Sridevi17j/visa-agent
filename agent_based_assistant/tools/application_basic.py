# Basic application information collection tool
# Purpose: Collect initial visa application data (country, purpose, dates, travelers)

from typing import Any, Dict, Optional
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from agent.state import AgentState, create_error_record
from config.settings import invoke_llm_safe


@tool
def base_information_collector_tool(user_message: str) -> str:
    """
    Collect basic visa application information: country, purpose, travel dates, number of travelers.
    
    Use this tool when:
    - User wants to start a visa application
    - User says "I want to apply for visa"
    - User provides application details that need extraction
    - Missing basic information needs to be collected
    
    Args:
        user_message: The user's input containing application details
    
    Returns:
        String response for collecting basic visa information
    """
    
    try:
        # Extract information from user message
        extracted_info = _extract_basic_visa_info_simple(user_message)
        
        # Check what information is still missing
        missing_fields = _get_missing_basic_fields(extracted_info)
        
        # If all basic info is collected, signal for visa type analysis
        if not missing_fields:
            return f"Perfect! I have collected all basic information:\n- Country: {extracted_info['country']}\n- Purpose: {extracted_info['purpose_of_travel']}\n- Travelers: {extracted_info['number_of_travelers']}\n- Dates: {extracted_info['travel_dates']}\n\nNow I need to analyze the best visa type for your travel needs. Let me check what visa options are available for your {extracted_info['country']} trip."
        
        # Generate question for missing information
        return _generate_missing_info_question(missing_fields, extracted_info)
        
    except Exception as e:
        return "I'm having difficulty processing your application details. Could you please tell me which country you want to visit and what is your purpose of travel?"


def _extract_basic_visa_info_simple(user_message: str) -> dict:
    """Extract basic visa information from user message using simple LLM"""
    try:
        extraction_prompt = f"""Extract visa application information from this user message: "{user_message}"

EXTRACT ONLY if explicitly mentioned in the message:
- Country name (if mentioned)
- Purpose of travel (tourism, business, work, study, transit, etc.)
- Number of travelers (convert "2 people", "solo trip"=1, "me and my wife"=2, "family of 4"=4)
- Travel dates (any format like "24/01/26 to 02/02/26", "next month", etc.)

Return in this exact format:
Country: [country name or "not mentioned"]
Purpose: [purpose or "not mentioned"]  
Travelers: [number or "not mentioned"]
Dates: [dates or "not mentioned"]

Only extract what is explicitly stated, do not assume or guess."""

        response = invoke_llm_safe([HumanMessage(content=extraction_prompt)])
        content = response.content.strip()
        
        # Parse the simple response format
        result = {}
        lines = content.split('\n')
        
        for line in lines:
            if line.startswith('Country:'):
                country = line.replace('Country:', '').strip()
                if country != "not mentioned":
                    result["country"] = country
                    
            elif line.startswith('Purpose:'):
                purpose = line.replace('Purpose:', '').strip()
                if purpose != "not mentioned":
                    result["purpose_of_travel"] = purpose
                    
            elif line.startswith('Travelers:'):
                travelers = line.replace('Travelers:', '').strip()
                if travelers != "not mentioned":
                    try:
                        result["number_of_travelers"] = int(travelers)
                    except:
                        pass
                        
            elif line.startswith('Dates:'):
                dates = line.replace('Dates:', '').strip()
                if dates != "not mentioned":
                    result["travel_dates"] = dates
        
        return result
        
    except Exception as e:
        return {}


# OLD PYDANTIC-BASED FUNCTION (REMOVED FOR LANGRAPH COMPATIBILITY)


def _get_missing_basic_fields(info: dict) -> list[str]:
    """Determine which basic fields are still missing"""
    missing = []
    
    if not info.get("country"):
        missing.append("country")
    if not info.get("purpose_of_travel"):
        missing.append("purpose_of_travel")
    if not info.get("number_of_travelers"):
        missing.append("number_of_travelers")
    if not info.get("travel_dates"):
        missing.append("travel_dates")
        
    return missing


def _generate_missing_info_question(missing_fields: list[str], current_info: dict) -> str:
    """Generate short, crisp question for missing basic information"""
    
    if not missing_fields:
        return "Perfect! I have collected all basic information. Now I need to analyze the best visa type for your travel needs. Let me check what visa options are available for your Vietnam trip."
    
    # Generate specific questions for missing fields
    questions = []
    if "country" in missing_fields:
        questions.append("Which country are you visiting?")
    if "purpose_of_travel" in missing_fields:
        questions.append("What is your purpose of travel? (e.g., tourism, business, work, study)")
    if "number_of_travelers" in missing_fields:
        questions.append("How many travelers?")
    if "travel_dates" in missing_fields:
        questions.append("What are your travel dates?")
    
    # Single question - direct and short
    if len(questions) == 1:
        return questions[0]
    
    # Multiple questions - simple format like original node
    numbered_questions = [f"{i+1}. {q}" for i, q in enumerate(questions)]
    return "\n".join(numbered_questions) + "\n\nPlease provide the missing information."


# Export the tool for agent use
__all__ = ["base_information_collector_tool"]