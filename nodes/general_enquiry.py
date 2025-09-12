import json
import os
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from state import State
from config.settings import llm
import pprint

class CountryExtraction(BaseModel):
    country: Optional[str] = Field(None, description="Extracted country name (lowercase, single word)")
    confidence: str = Field(description="High/Medium/Low confidence in extraction")

class VisaResponse(BaseModel):
    answer: str = Field(description="Direct answer to the visa question")

def extract_country_from_query(query: str) -> Optional[str]:
    """Extract country name from user query using LLM"""
    try:
        parser = PydanticOutputParser(pydantic_object=CountryExtraction)
        
        extraction_prompt = f"""Extract the country name from this visa-related query. Return the country name in lowercase, single word format (e.g., 'vietnam', 'thailand', 'singapore').

User Query: "{query}"

If no specific country is mentioned, set country to null.

{parser.get_format_instructions()}"""
        
        response = llm.invoke([HumanMessage(content=extraction_prompt)])
        extracted = parser.parse(response.content)
        
        return extracted.country if extracted.confidence != "Low" else None
        
    except Exception as e:
        print(f"Error extracting country: {e}")
        return None

def load_visa_knowledge(country: str) -> dict:
    """Load visa information from JSON knowledge base"""
    if not country:
        return {}
    
    knowledge_path = f"knowledge_base/{country}/visa_info.json"
    if os.path.exists(knowledge_path):
        try:
            with open(knowledge_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def format_visa_info_for_llm(visa_info: dict) -> str:
    """Format entire visa information JSON for LLM context using pprint"""
    if not visa_info:
        return "No specific visa information available."
    
    # Use pprint to format the entire JSON in a readable way
    formatted_json = pprint.pformat(visa_info, indent=2, width=100, depth=None)
    
    return f"COMPLETE VISA KNOWLEDGE BASE:\n{formatted_json}"

def general_enquiry(state: State) -> dict:
    """Handle general visa enquiries using knowledge base data"""
    try:
        user_message = state["messages"][-1].content
        
        country = extract_country_from_query(user_message)
        
        # If no country extracted from query, check if we have ongoing visa application context
        if not country and state.get("collection_in_progress"):
            incomplete_info = state.get("incomplete_initial_info", {})
            context_country = incomplete_info.get("country")
            if context_country:
                country = context_country.lower()
                print(f"Using context country: {country}")
        
        if not country:
            return {
                "messages": [AIMessage(content="I'd be happy to help with visa information! Could you please specify which country's visa you're asking about?")]
            }
        
        visa_info = load_visa_knowledge(country)
        
        if not visa_info:
            return {
                "messages": [AIMessage(content=f"I don't have detailed visa information for {country.title()} available at the moment. Please contact our support team for the most current information.")]
            }
        
        context = format_visa_info_for_llm(visa_info)
        
        parser = PydanticOutputParser(pydantic_object=VisaResponse)
        
        prompt = f"""You are a visa information specialist. Answer the user's question based ONLY on the provided visa information context.

CONTEXT:
{context}

USER QUESTION: {user_message}

Provide a helpful, accurate response. If the context doesn't contain enough information to fully answer the question, acknowledge this limitation.

{parser.get_format_instructions()}"""
        
        response = llm.invoke([HumanMessage(content=prompt)])
        parsed_response = parser.parse(response.content)
        
        result = {
            "messages": [AIMessage(content=parsed_response.answer)]
        }
        
        # If we came from visa collection flow, preserve context for routing back
        if state.get("collection_in_progress"):
            result["collection_in_progress"] = True
            result["incomplete_initial_info"] = state.get("incomplete_initial_info", {})
            result["previous_node"] = state.get("previous_node", "base_information_collector")
        
        return result
        
    except Exception as e:
        print(f"Error in general_enquiry: {e}")
        result = {
            "messages": [AIMessage(content="I'm having some technical difficulties right now. Please try your question again, or feel free to contact our support team for assistance.")]
        }
        
        # Preserve collection context even in error case
        if state.get("collection_in_progress"):
            result["collection_in_progress"] = True
            result["incomplete_initial_info"] = state.get("incomplete_initial_info", {})
            result["previous_node"] = state.get("previous_node", "base_information_collector")
        
        return result
