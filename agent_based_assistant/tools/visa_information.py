# Visa information tool for agent
# Purpose: Provide visa requirements, policies, and general country information

import json
import os
import pprint
from typing import Any, Dict, Optional
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from agent.state import AgentState
from config.settings import invoke_llm_safe


@tool
def general_enquiry_tool(user_message: str) -> str:
    """
    Provide visa information, requirements, and policies for specific countries.
    
    Use this tool when:
    - User asks about visa requirements for a country
    - User wants to know processing times, fees, or documentation
    - User asks general visa policy questions
    - User needs information about entry requirements
    
    Args:
        user_message: The user's visa information query
    
    Returns:
        String response with visa information that the agent can use
    """
    
    try:
        # Extract country from user query
        country = _extract_country_from_query(user_message)
        
        # If still no country, ask for clarification
        if not country:
            return "I'd be happy to help with visa information! Could you please specify which country's visa you're asking about?"
        
        # Load and process visa information
        visa_info = _load_visa_knowledge(country)
        
        if not visa_info:
            return f"I don't have detailed visa information for {country.title()} available at the moment. Please contact our support team for the most current information."
        
        # Generate response using LLM with visa knowledge
        response = _generate_visa_response(user_message, visa_info)
        
        return response
        
    except Exception as e:
        return "I'm having some technical difficulties right now. Please try your question again, or feel free to contact our support team for assistance."


def _extract_country_from_query(query: str) -> Optional[str]:
    """Extract country name from user query using LLM"""
    try:
        extraction_prompt = f"""Extract the country name from this visa-related query. Return ONLY the country name in lowercase, single word format (e.g., 'vietnam', 'thailand', 'singapore').

User Query: "{query}"

If no specific country is mentioned, return 'none'.

Response format: Just the country name, nothing else."""
        
        response = invoke_llm_safe([HumanMessage(content=extraction_prompt)])
        country = response.content.strip().lower()
        
        # Simple validation - if it looks like a country name
        if country and country != 'none' and len(country) > 2 and country.isalpha():
            return country
        
        return None
        
    except Exception as e:
        return None


def _load_visa_knowledge(country: str) -> dict:
    """Load visa information from JSON knowledge base"""
    if not country:
        return {}
    
    # Look for knowledge base in the current directory (agent_based_assistant)
    knowledge_path = f"knowledge_base/{country}/visa_info.json"
    
    if os.path.exists(knowledge_path):
        try:
            with open(knowledge_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    
    return {}


def _format_visa_info_for_llm(visa_info: dict) -> str:
    """Format entire visa information JSON for LLM context"""
    if not visa_info:
        return "No specific visa information available."
    
    # Use pprint to format the entire JSON in a readable way
    formatted_json = pprint.pformat(visa_info, indent=2, width=100, depth=None)
    
    return f"COMPLETE VISA KNOWLEDGE BASE:\n{formatted_json}"


def _generate_visa_response(user_message: str, visa_info: dict) -> str:
    """Generate structured visa response using LLM and knowledge base"""
    try:
        context = _format_visa_info_for_llm(visa_info)
        
        prompt = f"""You are a professional visa assistant. Answer the user's question based ONLY on the provided visa information context.

CONTEXT:
{context}

USER QUESTION: {user_message}

RESPONSE FORMAT EXAMPLE:
When someone asks "What are the Vietnam visa requirements?", you should respond like this:

**Documents Required**
- Valid passport (6+ months validity)
- Recent passport photos
- Completed application form

**Pricing**
- Single entry: $25 USD
- Multiple entry: $50 USD

**Number of Days Stay**
- Up to 30 days per entry

**Visa Validity**
- 90 days from issue date

**Processing Time**
- 3-5 business days

This is an example - you need to provide customized responses like this for every question. Always structure your answers with clear headings and bullet points. Keep responses crisp, organized, and professional. For specific questions (like entry ports, document details), provide direct, concise answers in the same structured format.

For any question related to visa, you need to answer like a Highly experienced Visa Assistant, with correct and appropriate short details.

Return ONLY the answer text, no JSON formatting."""
        
        response = invoke_llm_safe([HumanMessage(content=prompt)])
        return response.content.strip()
        
    except Exception as e:
        return "I encountered an issue while processing your visa information request. Please try asking your question again or contact our support team."


# Export the tool for agent use
__all__ = ["general_enquiry_tool"]