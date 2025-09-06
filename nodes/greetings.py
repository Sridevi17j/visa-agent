from state import State
from langchain_core.messages import AIMessage

def greetings(state:State) -> dict:
    return {"messages": [AIMessage(content="Hello, I am Veazy, VISA Genie! How can I assist you today?")]}
