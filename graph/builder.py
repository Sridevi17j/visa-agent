from langgraph.graph import StateGraph, START, END
from state import State
from nodes.intent_analyzer import intent_analyser
from nodes.greetings import greetings
from nodes.general_enquiry import general_enquiry
from nodes.visa_application import visa_application
from nodes.base_information_collector import base_information_collector
from nodes.collection_resume import collection_resume, handle_resume_decision
from nodes.detailed_collector import detailed_collector
from nodes.docs_parser import docs_parser

def build_graph(checkpointer=None):
    graph = StateGraph(State)
    
    graph.add_node("intent_analyser", intent_analyser)
    graph.add_node("greetings", greetings)
    graph.add_node("general_enquiry", general_enquiry)
    graph.add_node("visa_application", visa_application)
    graph.add_node("base_information_collector", base_information_collector)
    graph.add_node("collection_resume", collection_resume)
    graph.add_node("handle_resume_decision", handle_resume_decision)
    graph.add_node("detailed_collector", detailed_collector)
    graph.add_node("docs_parser", docs_parser)
    
    graph.add_edge(START, "intent_analyser")
    graph.add_conditional_edges(
        "intent_analyser", 
        lambda state: state.get("next", "greetings"),
        {
            "greetings": "greetings", 
            "general_enquiry": "general_enquiry", 
            "visa_application": "visa_application",
            "base_information_collector": "base_information_collector",
            "handle_resume_decision": "handle_resume_decision",
            "docs_parser": "docs_parser"
        }
    )
    
    graph.add_edge("greetings", END)
    
    graph.add_conditional_edges(
        "general_enquiry",
        lambda state: "collection_resume" if state.get("collection_in_progress") else "__end__",
        {
            "collection_resume": "collection_resume",
            "__end__": END
        }
    )
    
    graph.add_edge("visa_application", "base_information_collector")
    
    graph.add_conditional_edges(
        "base_information_collector",
        lambda state: state.get("next", "__end__"),
        {
            "continue_collection": "base_information_collector",
            "base_information_collector": "base_information_collector",  # Self-reference for routing from other nodes
            "detailed_collector": "detailed_collector", 
            "intent_analyser": "intent_analyser",
            "proceed_to_next_step": "__end__",
            "__end__": END
        }
    )
    
    graph.add_edge("detailed_collector", "docs_parser")
    
    graph.add_conditional_edges(
        "docs_parser",
        lambda state: state.get("next", "__end__"),
        {
            "continue_collection": "docs_parser",  # If more documents needed
            "__end__": END
        }
    )
    
    graph.add_conditional_edges(
        "collection_resume",
        lambda state: state.get("next", "__end__"),
        {
            "handle_resume_decision": "handle_resume_decision",
            "base_information_collector": "base_information_collector",
            "__end__": END
        }
    )
    
    graph.add_conditional_edges(
        "handle_resume_decision",
        lambda state: state.get("next", "__end__"),
        {
            "base_information_collector": "base_information_collector",
            "intent_analyser": "intent_analyser",
            "__end__": END
        }
    )
    
    return graph.compile(checkpointer=checkpointer)
