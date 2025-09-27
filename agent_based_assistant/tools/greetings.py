# Greeting tools for visa assistant agent
# Purpose: Handle user greetings and introductions

import os
from typing import Any, Dict
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from agent.state import AgentState


@tool
def greetings_tool(user_message: str) -> str:
    """
    Handle user greetings, general conversation, and off-topic questions.
    
    Use this tool when:
    - User says "hi", "hello", "hey", or other greetings
    - User asks off-topic questions unrelated to visas
    - User needs clarification about what you can help with
    - General conversation or small talk
    
    Args:
        user_message: The user's input message
    
    Returns:
        String response that the agent can use to formulate a natural reply
    """
    
    # Determine appropriate greeting response
    response = _generate_greeting_response(user_message)
    
    return response


def _generate_greeting_response(user_message: str) -> str:
    """Generate appropriate greeting response"""
    
    message_lower = user_message.lower().strip()
    
    # Handle different types of greetings
    if any(greeting in message_lower for greeting in ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]):
        return "Hello! I'm Veazy, your VISA Genie assistant. I'm here to help you with visa information and applications.\n\n1. I can answer any visa-related queries\n2. I can complete your entire visa application on your behalf\n\nWhat can I assist you with today?"
    
    # Handle thanks/appreciation
    elif any(thanks in message_lower for thanks in ["thank", "thanks", "appreciate"]):
        return "You're welcome! Feel free to ask me anything about visa requirements, applications, or if you'd like to start a new application."
    
    # Handle farewell
    elif any(bye in message_lower for bye in ["bye", "goodbye", "see you", "farewell"]):
        return "Goodbye! Feel free to return anytime if you need help with visa information or applications. Have a great day!"
    
    # Handle off-topic questions
    elif _is_off_topic(message_lower):
        return "I specialize in helping with visa information and applications. While I'd love to chat about other topics, I'm most helpful with visa-related questions. What can I assist you with regarding visas today?"
    
    # Handle unclear input
    elif len(message_lower) < 3 or not message_lower.replace(" ", "").isalpha():
        return "I didn't quite catch that. I'm here to help with visa information and applications. Could you let me know what specific visa assistance you need?"
    
    # Default friendly response for unclear greetings
    else:
        return "Hello! I'm Veazy, your visa assistant. I can help you with visa requirements, country information, and visa applications. What would you like to know about visas today?"


def _is_off_topic(message_lower: str) -> bool:
    """Detect if message is off-topic from visa assistance"""
    
    off_topic_indicators = [
        "weather", "sports", "movies", "music", "food", "cooking", "games", 
        "programming", "code", "technology", "politics", "news", "stocks",
        "health", "medicine", "dating", "relationships", "jokes", "funny",
        "shopping", "fashion", "cars", "driving", "pets", "animals"
    ]
    
    # Check if message contains off-topic keywords without visa context
    has_off_topic = any(indicator in message_lower for indicator in off_topic_indicators)
    has_visa_context = any(visa_word in message_lower for visa_word in ["visa", "travel", "passport", "country", "application"])
    
    return has_off_topic and not has_visa_context


# Export the tool for agent use
__all__ = ["greetings_tool"]