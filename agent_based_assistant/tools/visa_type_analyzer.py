# Visa type analyzer tool using Groq API
# Purpose: Analyze travel details and recommend appropriate visa type

import os
from typing import Any
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq


def _get_groq_llm():
    """Initialize Groq LLM for visa type analysis"""
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        
        return ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=api_key,
            temperature=0.2,
            max_tokens=512,
            timeout=30
        )
    except Exception as e:
        print(f"Groq LLM initialization failed: {e}")
        return None


@tool
def visa_type_analyzer_tool(country: str, purpose: str, travelers: int, travel_dates: str) -> str:
    """
    Analyze travel details and recommend the most appropriate visa type using Groq API.
    
    Use this tool after collecting basic travel information to determine
    which visa type best suits the traveler's needs.
    
    Args:
        country: Destination country name
        purpose: Purpose of travel (tourism, business, work, study, etc.)
        travelers: Number of people traveling  
        travel_dates: Travel dates in natural language format
    
    Returns:
        String response with visa type recommendation that the agent can use
    """
    
    try:
        # Initialize Groq LLM
        groq_llm = _get_groq_llm()
        if not groq_llm:
            return _get_fallback_response(country, purpose)
        
        # Create prompt for Groq API
        prompt = f"""You are a visa expert. Analyze these travel details and recommend the most appropriate visa type:

**Travel Details:**
- Country: {country}
- Purpose: {purpose}
- Travelers: {travelers} people
- Travel dates: {travel_dates}

**Task:** Recommend the specific visa type with practical details.

**Response Format:**
**Recommended Visa Type**: [Specific visa name]
**Validity**: [How long visa is valid]
**Cost**: [Approximate fee in USD]
**Processing Time**: [How long to process]
**Best For**: [Why this suits their needs]

Keep response concise and practical. Focus on the most suitable single recommendation."""

        # Call Groq API
        response = groq_llm.invoke([HumanMessage(content=prompt)])
        
        if response and response.content:
            return response.content.strip()
        else:
            return _get_fallback_response(country, purpose)
            
    except Exception as e:
        print(f"Groq API error in visa_type_analyzer_tool: {e}")
        return _get_fallback_response(country, purpose)


def _get_fallback_response(country: str, purpose: str) -> str:
    """Fallback response when Groq API is unavailable"""
    
    return f"""I'm unable to access the visa analysis service right now. Based on your travel to {country} for {purpose}, I recommend:

**General Recommendation**: Check the official {country} embassy website for current visa requirements as they vary by nationality.

**Next Steps**:
1. Verify your nationality's visa requirements
2. Choose appropriate visa type for {purpose}
3. Check processing times and costs
4. Gather required documents

Would you like to continue with the general application process, or prefer to research visa types first?"""


# Export the tool
__all__ = ["visa_type_analyzer_tool"]