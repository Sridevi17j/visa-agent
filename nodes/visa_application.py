from state import State

def visa_application(state:State) -> dict:
    return {
        "messages": "I can help you with your visa application. Let me collect the basic information first.",
        "next": "visa_application_collector"
    }
