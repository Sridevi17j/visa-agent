from graph.builder import build_graph
from langchain_core.messages import HumanMessage

def main():
    app = build_graph()
    state = {"messages": []}

    while True:
        user_input = input("User: ")
        
        # Add user message to state using proper LangChain message object
        previous_message_count = len(state["messages"])
        state["messages"].append(HumanMessage(content=user_input))
        
        # Invoke the app with the accumulated state
        agent_answer = app.invoke(state)
        
        # Show all new assistant messages since the last user input
        new_messages = agent_answer["messages"][previous_message_count + 1:]  # Skip user message + previous messages
        for msg in new_messages:
            if hasattr(msg, 'type') and msg.type == 'ai':
                print("Assistant:", msg.content)
        
        # Update state with the response
        state = agent_answer

if __name__ == "__main__":
    main()
