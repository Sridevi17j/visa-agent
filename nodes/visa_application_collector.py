from state import State
from config.settings import llm
from config.visa_types import COMBINED_VISA_TYPES
from langchain_core.messages import SystemMessage, HumanMessage

def visa_application_collector(state: State) -> dict:

    user_message = state["messages"][0].content
    system_prompt = SystemMessage(content=f"""
    Analyze this user message: "{user_message}"
    
    Check what visa application information is present:
    1. Country/destination name
    2. Number of travelers
    3. Visa type from these options: {', '.join(COMBINED_VISA_TYPES)}
    
    For missing information, ask the appropriate questions:
    - If country missing: "Which country are you visiting?"
    - If travelers missing: "How many travelers?"
    - If visa type missing: "What type of visa do you need? Options: {', '.join(COMBINED_VISA_TYPES)}"
    
    Instructions:
    - If ALL information is present, respond: "Perfect! I have all the required information for your visa application."
    - If some information is missing, ask ONLY for the missing information
    - Be conversational and helpful
    - List missing questions clearly
    """)
    
    result = llm.invoke([system_prompt, HumanMessage(content=user_message)])
    
    return {"messages": result.content}
