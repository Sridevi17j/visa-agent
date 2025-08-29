from state import State
from config.settings import llm
from utils.prompts import system_prompt

def intent_analyser(state:State) -> dict:
    user_message = state["messages"][-1].content
    
    if state.get("incomplete_session_id") and user_message.lower().strip() in ["yes", "y", "no", "n", "continue", "proceed", "start over"]:
        return {"next": "handle_resume_decision"}
    
    result = {"messages":llm.invoke([system_prompt, user_message])}
    result_type = result["messages"].content
    if result_type == "greetings":
        return {"next": "greetings"}
    elif result_type == "general_enquiry":
        return {"next": "general_enquiry"}
    else:
        return {"next": "visa_application"}
