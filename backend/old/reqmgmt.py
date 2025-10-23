import os
from langchain_groq import ChatGroq
from langchain_neo4j import Neo4jGraph
from langgraph.graph import StateGraph, MessagesState, END
from langchain_core.messages import SystemMessage
from pydantic import BaseModel, Field
from typing import List, Annotated
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode

# -----------------------------
# Environment setup
# -----------------------------
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = ""
os.environ["LANGCHAIN_PROJECT"] = "reqmgmt"
os.environ["GROQ_API_KEY"] = ""

llm = ChatGroq(model="openai/gpt-oss-120b")

# Initialize Neo4j connection
graph_db = Neo4jGraph(
    url="bolt://localhost:7687",
    username="neo4j",
    password="12345678",
    database="requirements-management",
    enhanced_schema=True
)

print("Neo4j Schema:")
print(graph_db.schema)
print("\n" + "="*80 + "\n")

# -----------------------------
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
    project_name: str = "LangGraph_Project"

# -----------------------------
# Tool Definition
# -----------------------------
@tool
def save_to_neo4j(
    requirements: Annotated[List[str], "List of requirements to save"],
    risks: Annotated[List[str], "List of risks to save"],
    project_name: Annotated[str, "Name of the project"],
    keyword: Annotated[str, "Selected keyword for the requirements"]
) -> str:
    """
    Save requirements and risks to Neo4j database with relationships.
    Creates Project, Requirement, Risk nodes and their relationships.
    """
    try:
        # Create Project node
        graph_db.query("""
            MERGE (p:Project {name: $project_name})
            SET p.keyword = $keyword,
                p.created_at = datetime()
            RETURN p
        """, {"project_name": project_name, "keyword": keyword})
        
        # Create Requirements and link to Project
        for idx, req in enumerate(requirements, 1):
            graph_db.query("""
                MATCH (p:Project {name: $project_name})
                MERGE (r:Requirement {
                    description: $desc,
                    project: $project_name,
                    index: $idx
                })
                MERGE (p)-[:HAS_REQUIREMENT]->(r)
                RETURN r
            """, {"desc": req, "project_name": project_name, "idx": idx})
        
        # Create Risks and link to corresponding Requirements
        for idx, risk in enumerate(risks, 1):
            graph_db.query("""
                MATCH (p:Project {name: $project_name})
                MATCH (r:Requirement {project: $project_name, index: $idx})
                MERGE (rk:Risk {
                    description: $desc,
                    project: $project_name,
                    index: $idx
                })
                MERGE (r)-[:HAS_RISK]->(rk)
                MERGE (p)-[:HAS_RISK]->(rk)
                RETURN rk
            """, {"desc": risk, "project_name": project_name, "idx": idx})
        
        return f"✅ Successfully saved {len(requirements)} requirements and {len(risks)} risks to Neo4j for project '{project_name}'"
    
    except Exception as e:
        return f"❌ Error saving to Neo4j: {str(e)}"

# Create tool node
tools = [save_to_neo4j]
tool_node = ToolNode(tools)

# -----------------------------
# Graph Nodes
# -----------------------------
def generate_keywords(state: KeywordState):
    print("\n✅ ================ Generating Keywords ===============================")
    
    prompt = ChatPromptTemplate.from_template("""
    You are an expert requirement analyst.  
    Given the following requirement description:
    "{requirement_description}"
    
    Generate exactly 5 keywords, each containing 3 words, as JSON list.
    """)
    
    llm_structured = llm.with_structured_output(KeywordOutput)
    result = (prompt | llm_structured).invoke({"requirement_description": state["requirement_description"]})
    
    state["keyword_output"] = result
    state["messages"].append(SystemMessage(content=f"Generated keywords: {result.keywords}"))
    
    print("\n📋 Generated Keywords:")
    for i, kw in enumerate(result.keywords, 1):
        print(f"  {i}. {kw}")
    
    return state

def human_feedback(state: KeywordState):
    print("\n✅ ================ Human Feedback ===============================")
    print("\n🔍 Available Keywords:")
    for i, kw in enumerate(state["keyword_output"].keywords, 1):
        print(f"  {i}. {kw}")
    
    while True:
        try:
            choice = input("\n👉 Select a keyword by number (1-5): ").strip()
            choice_idx = int(choice) - 1
            
            if 0 <= choice_idx < len(state["keyword_output"].keywords):
                state["selected_keyword"] = state["keyword_output"].keywords[choice_idx]
                print(f"\n✓ Selected: {state['selected_keyword']}")
                break
            else:
                print("❌ Invalid choice. Please select a number between 1 and 5.")
        except (ValueError, IndexError):
            print("❌ Invalid input. Please enter a number between 1 and 5.")
    
    return state

def should_continue(state):
    if state["selected_keyword"] and state["selected_keyword"].strip():
        return "generate_requirements"
    return END

def generate_requirements(state: KeywordState):
    print("\n✅ ================ Generating Requirements ===============================")
    
    prompt = ChatPromptTemplate.from_template("""
    You are an expert requirement analyst.  
    Given the requirement description "{requirement_description}" and keyword "{selected_keyword}", 
    generate 5 formal requirements. Ensure varied formal requirement tone for each requirement. 
    Ensure to generate the requirements as JSON list.
    """)
    
    llm_structured = llm.with_structured_output(RequirementsOutput)
    result = (prompt | llm_structured).invoke({
        "selected_keyword": state["selected_keyword"],
        "requirement_description": state["requirement_description"]
    })
    
    state["requirements_output"] = result
    state["messages"].append(SystemMessage(content=f"Generated requirements: {result.requirements}"))
    
    print("\n📝 Generated Requirements:")
    for i, req in enumerate(result.requirements, 1):
        print(f"  {i}. {req}")
    
    return state

def generate_risks(state: KeywordState):
    print("\n✅ ================ Generating Risks ===============================")
    
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
        "requirements": state["requirements_output"].requirements
    })
    
    state["risks_output"] = result
    state["messages"].append(SystemMessage(content=f"Generated risks: {result.Risks}"))
    
    print("\n⚠️  Generated Risks:")
    for i, risk in enumerate(result.Risks, 1):
        print(f"  {i}. {risk}")
    
    return state

def call_save_tool(state: KeywordState):
    print("\n✅ ================ Saving to Neo4j ===============================")
    
    # Prepare tool call
    result = save_to_neo4j.invoke({
        "requirements": state["requirements_output"].requirements,
        "risks": state["risks_output"].Risks,
        "project_name": state["project_name"],
        "keyword": state["selected_keyword"]
    })
    
    print(f"\n{result}")
    state["messages"].append(SystemMessage(content=result))
    
    return state

# -----------------------------
# Build Graph
# -----------------------------
builder = StateGraph(KeywordState)

# Add nodes
builder.add_node("generate_keywords", generate_keywords)
builder.add_node("human_feedback", human_feedback)
builder.add_node("generate_requirements", generate_requirements)
builder.add_node("generate_risks", generate_risks)
builder.add_node("save_to_db", call_save_tool)

# Add edges
builder.add_edge("generate_keywords", "human_feedback")
builder.add_conditional_edges(
    "human_feedback",
    should_continue,
    {
        "generate_requirements": "generate_requirements",
        END: END
    }
)
builder.add_edge("generate_requirements", "generate_risks")
builder.add_edge("generate_risks", "save_to_db")
builder.add_edge("save_to_db", END)

# Set entry point
builder.set_entry_point("generate_keywords")

# Compile with memory
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

# -----------------------------
# Run Graph
# -----------------------------
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 Starting Requirements Management Workflow")
    print("="*80 + "\n")
    
    state = {
        "requirement_description": "The benefits of adopting LangGraph as an agent framework",
        "messages": [],
        "keyword_output": None,
        "selected_keyword": None,
        "requirements_output": None,
        "risks_output": None,
        "project_name": "LangGraph_Adoption_2025"
    }
    
    thread = {"configurable": {"thread_id": 1}}
    
    # Stream through the graph
    for event in graph.stream(state, thread, stream_mode="values"):
        pass  # Printing is handled in individual nodes
    
    print("\n" + "="*80)
    print("✅ Workflow Complete!")
    print("="*80 + "\n")