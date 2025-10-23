import os
from langchain_groq import ChatGroq
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
from langgraph.graph import StateGraph, MessagesState, END
from langchain_core.messages import SystemMessage
from pydantic import BaseModel, Field
from typing import List
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.prompts import ChatPromptTemplate
import getpass
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = ""
os.environ["LANGCHAIN_PROJECT"] = "reqmgmt"
os.environ["GROQ_API_KEY"] = ""
# if "GROQ_API_KEY" not in os.environ:    
#     os.environ["GROQ_API_KEY"] = getpass.getpass("")
llm = ChatGroq(
    model="openai/gpt-oss-120b")

graph = Neo4jGraph(url="bolt://localhost:7687", username="neo4j", password="", database ="requirements-management", enhanced_schema=True)

print(graph.schema)


# Pydantic Models
# -----------------------------
class KeywordOutput(BaseModel):
    keywords: List[str] = Field(..., description="5 keywords, each 3 words long")

class RequirementsOutput(BaseModel):
    requirements: List[str] = Field(..., description="5 formal requirements derived from selected keyword")


class RisksOutput(BaseModel):
    Risks: List[str] = Field(..., description="1 Risk derived from each requirement")



# -----------------------------
# Graph State
# -----------------------------
class KeywordState(MessagesState):
    requirement_description: str
    keyword_output: KeywordOutput | None = None
    selected_keyword: str | None = None
    requirements_output: RequirementsOutput | None = None
    risks_output: RisksOutput | None = None


# -----------------------------
# Nodes (example placeholders)
# -----------------------------
def generate_keywords(state: KeywordState):
    # LLM call logic here

    from langchain_core.prompts import ChatPromptTemplate

    print("\n✅ ================Entered Generated Keywords===============================:")
    prompt = ChatPromptTemplate.from_template("""
    You are an expert requirement analyst.  
    Given the following requirement description:

    "{requirement_description}"

    Generate exactly 5 keywords, each containing 3 words, as JSON list.
    """)

    # Use structured output
    llm_structured = llm.with_structured_output(KeywordOutput)
    result = (prompt | llm_structured).invoke({"requirement_description": state["requirement_description"]})

    state["keyword_output"] = result
    state["messages"].append(SystemMessage(content=f"Generated keywords: {result.keywords}"))


    print("=== Current State ===")
    for k, v in state.items():
        print(f"{k}: {v}")
    return state


def human_feedback(state: KeywordState):

    """Interrupt node: user selects keyword"""
    print("\n✅ ================Entered human feedback===============================:")
 
    # for i, kw in enumerate(state["keyword_output"].keywords, 1):
    #     print(f"{i}. {kw}")

    while True:
        choice = input("Select a keyword by number: ")
        # print("choice is ",choice)
        # print("you have selected", state["keyword_output"].keywords[int(choice)-1])
        #if choice.isdigit() and 1 <= int(choice) <= len(state["keyword_output"].keywords):
        state["selected_keyword"] = state["keyword_output"].keywords[int(choice)-1]
        # print(state.selected_keyword) 
        break
    
    print("=== Current State ===")
    for k, v in state.items():
        print(f"{k}: {v}")
    return state

def should_continue(state):
    print("\n✅ ================Entered should continue===============================:")
    feedback = (state["selected_keyword"] or "").strip().lower()
    if feedback and feedback not in ["", "none", "skip", "done", "continue"]:
        return "generate_requirements"
    return END

def generate_requirements(state: KeywordState):
    # LLM call logic to generate 5 requirements
    print("\n✅ ================Entered generate_requirements===============================:")
    prompt = ChatPromptTemplate.from_template("""
    You are an expert requirement analyst.  
    Given the requirement description "{requirement_description}" and keyword "{selected_keyword}", generate 5 formal requirements.Ensure varied formal requirement tone for each requirement. Ensure to generate the requirements as as JSON list
    """)
    llm_structured = llm.with_structured_output(RequirementsOutput)
    #print("llm_structured is ", llm_structured)
    result = (prompt | llm_structured).invoke({
    "selected_keyword": state["selected_keyword"],
    "requirement_description": state["requirement_description"]
})
    #print("result is ", result)
    state["requirements_output"] = result

    #print("state.requirements_output is ", state["requirements_output"])
    #print("result.requirements is ", result.requirements)
    
    state["messages"].append(SystemMessage(content=f"Generated requirements: {result.requirements}"))

    print("=== Current State ===")
    for k, v in state.items():
        print(f"{k}: {v}")
    return state

def generate_risks(state: KeywordState):
    from langchain_core.prompts import ChatPromptTemplate

    print("\n✅ ================Entered Generated Risks===============================:")
    print("=== Current State ===")
    print(state)

    requirements_list = state["requirements_output"].requirements

    prompt = ChatPromptTemplate.from_template("""
You are a risk analysis expert specializing in AI frameworks. 
Based on the following requirements:

{requirements}

Generate exactly 5 risks (one corresponding to each requirement).
Your response MUST be valid JSON and follow this exact format:

{{
  "Risks": [
    "risk for requirement 1",
    "risk for requirement 2",
    "risk for requirement 3",
    "risk for requirement 4",
    "risk for requirement 5"
  ]
}}
Ensure there are exactly 5 risks, no additional fields, no markdown, no explanations.
""")

    llm_structured = llm.with_structured_output(RisksOutput)

    result = (prompt | llm_structured).invoke({
        "requirements": requirements_list
    })

    # Save result to state
    state["risks_output"] = result
    state["messages"].append(
        SystemMessage(content=f"Generated risks: {result.Risks}")
    )

    print("--- Risks Generated Successfully ---")
    for idx, r in enumerate(result.Risks, 1):
        print(f"{idx}. {r}")

    return state


# -----------------------------
# Build Graph
# -----------------------------
builder = StateGraph(KeywordState)
builder.add_node("generate_keywords", generate_keywords)
builder.add_node("human_feedback", human_feedback)
builder.add_node("generate_requirements", generate_requirements)
builder.add_node("generate_risks", generate_risks)

builder.add_edge("generate_keywords", "human_feedback")
# builder.add_edge("human_feedback", "generate_requirements")
# builder.add_edge("generate_requirements", END)


builder.add_conditional_edges("human_feedback",
                        should_continue,
                        ["generate_keywords",
                        "generate_requirements"])
builder.add_edge("human_feedback", "generate_requirements")
builder.add_edge("generate_requirements", "generate_risks")
builder.add_edge("generate_risks", END)


builder.set_entry_point("generate_keywords")

# -----------------------------
# Compile graph with memory & interrupt
# -----------------------------
memory = MemorySaver()
graph = builder.compile( checkpointer=memory)



# -----------------------------
# Run with thread isolation
# -----------------------------
thread = {"configurable": {"thread_id": 1}}


# from IPython.display import Image, display

# # Draw the graph as a Mermaid PNG
# graph_image = graph.get_graph().draw_mermaid_png()

# # Display inline in notebook
# display(Image(graph_image))

# Example LLM Usage
if __name__ == "__main__":
    
    state = {
        "requirement_description": "The benefits of adopting LangGraph as an agent framework",
        "messages": [],
        "keyword_output": None,
        "selected_keyword": None,
        "requirements_output": None,
        "risks_output": None
    }

# Run the entire graph; input() will pause it once
for event in graph.stream(state, thread, stream_mode="values"):

    print("event", event)
    if "keyword_output" in event and event["keyword_output"]:
        # print("\n⚡ Current Keywords:")
        print(" -----------------------------")
        for kw in event["keyword_output"].keywords:
            
            print(" -", kw)
    if "requirements_output" in event and event["requirements_output"]:
        print(" -----------------------------")
        # print("\n✅ Final Generated Requirements:")
        for kw1 in event["requirements_output"].requirements:           
            print(" -", kw1)
    if "risks_output" in event and event["risks_output"]:
        print(" -----------------------------")
        # print("\n✅ Final Generated Requirements:")
        for kw1 in event["risks_output"].Risks:           
            print(" -", kw1)
    # if "requirements_output" in event and event["requirements_output"]:
    #     # print("\n✅ Final Generated Requirements:")
    #     for i, req in enumerate(event["requirements_output"].requirements, 1):
    #         print(f"{i}. {req}")


