"""LangGraph workflow definition."""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from nodes import (
    KeywordState,
    generate_keywords,
    generate_requirements,
    generate_risks,
    call_save_tool
)
from logger import logger

def should_regenerate(state: KeywordState) -> str:
    """Check regeneration flag."""
    regenerate_flag = state.get("regenerate_flag")
    
    if regenerate_flag == "requirements":
        logger.info("Routing to regenerate requirements")
        return "generate_requirements"
    elif regenerate_flag == "risks":
        logger.info("Routing to regenerate risks")
        return "generate_risks"
    elif regenerate_flag == "both":
        logger.info("Routing to regenerate both")
        return "generate_requirements"
    
    logger.info("Routing to save")
    return "save_to_db"

def build_graph():
    """Build and compile workflow."""
    logger.info("Building workflow graph")
    
    builder = StateGraph(KeywordState)
    
    # Add all nodes
    builder.add_node("generate_keywords", generate_keywords)
    builder.add_node("generate_requirements", generate_requirements)
    builder.add_node("generate_risks", generate_risks)
    builder.add_node("save_to_db", call_save_tool)
    
    # Simple linear flow with optional regeneration
    builder.add_edge("generate_keywords", END)  # Keywords stop here, wait for selection
    builder.add_edge("generate_requirements", "generate_risks")  # Requirements -> Risks
    
    # After risks, check if we need to regenerate or save
    builder.add_conditional_edges(
        "generate_risks",
        should_regenerate,
        {
            "generate_requirements": "generate_requirements",
            "generate_risks": "generate_risks",
            "save_to_db": "save_to_db"
        }
    )
    
    builder.add_edge("save_to_db", END)  # Save and end
    
    # Entry point
    builder.set_entry_point("generate_keywords")
    
    # Compile with memory
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)
    
    logger.info("Graph built successfully")
    return graph

workflow_graph = build_graph()