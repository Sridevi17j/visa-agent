from state import State
from langchain_core.messages import AIMessage

def visa_application(state:State) -> dict:
    return {
        "messages": [AIMessage(content="I can help you with your visa application. Let me collect the basic information first.")],
        "next": "base_information_collector"
    }
