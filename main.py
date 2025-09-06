from graph.builder import build_graph
from langchain_core.messages import HumanMessage

def main():
    app = build_graph()
    state = {"messages": []}

    while True:
        user_input = input("User: ")
        
        # Add user message to state using proper LangChain message object
        state["messages"].append(HumanMessage(content=user_input))
        
        # Invoke the app with the accumulated state
        agent_answer = app.invoke(state)
        
        # Update state with the response
        state = agent_answer
        
        print("Assistant:", agent_answer["messages"][-1].content)

if __name__ == "__main__":
    main()
