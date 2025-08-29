from graph.builder import build_graph

def main():
    app = build_graph()

    while True:
        user_input = input("User: ")
        agent_answer=app.invoke({"messages" : [{"role": "user", "content": user_input }]})
        print("Assistant:", agent_answer["messages"][-1].content)

if __name__ == "__main__":
    main()
