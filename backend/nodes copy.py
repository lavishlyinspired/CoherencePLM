# =============================================================================
# FILE: nodes.py (REPLACE EXISTING)
# =============================================================================
"""LangGraph node definitions."""
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from langgraph.graph import MessagesState
from typing import Optional
from config import settings
from models import KeywordOutput, RequirementsOutput, RisksOutput
from logger import logger
from tools import save_to_neo4j
# Use JSON mode instead of structured output
llm = ChatGroq(
    model="qwen/qwen3-32b",  # This model supports JSON mode better
    temperature=0.7
)
class KeywordState(MessagesState):
    """State for workflow."""
    requirement_description: str
    keyword_output: Optional[KeywordOutput] = None
    selected_keyword: Optional[str] = None
    requirements_output: Optional[RequirementsOutput] = None
    risks_output: Optional[RisksOutput] = None
    project_name: str = "Default_Project"
    regenerate_flag: Optional[str] = None

def generate_keywords(state: KeywordState) -> KeywordState:
    """Generate keywords from requirement description."""
    logger.info("Generating keywords")
    
    prompt = ChatPromptTemplate.from_template("""
    You are an expert requirement analyst.  
    Given the following requirement description:
    "{requirement_description}"
    
    Generate exactly 5 keywords, each containing 3 words, as JSON list.
    """)
    
    
    try:
        llm_structured = llm.with_structured_output(KeywordOutput)
        result = (prompt | llm_structured).invoke({
            "requirement_description": state["requirement_description"]
        })
        
        state["keyword_output"] = result
        state["messages"].append(SystemMessage(content=f"Keywords: {result.keywords}"))
        logger.info(f"Generated {len(result.keywords)} keywords")
        
        for i, kw in enumerate(result.keywords, 1):
            logger.debug(f"  Keyword {i}: {kw}")
        
        return state
    except Exception as e:
        logger.error(f"Error generating keywords: {e}", exc_info=True)
        raise

def generate_requirements(state: KeywordState) -> KeywordState:
    """Generate requirements from selected keyword."""
    logger.info(f"Generating requirements for: {state['selected_keyword']}")
    
    prompt = ChatPromptTemplate.from_template("""
        You are an expert requirement analyst.  
        Given the requirement description "{requirement_description}" and keyword "{selected_keyword}", 
        generate 5 formal requirements. Ensure varied formal requirement tone for each requirement. 
        Ensure to generate the requirements as JSON list.
        """)
    
    try:
        llm_structured = llm.with_structured_output(RequirementsOutput)
        result = (prompt | llm_structured).invoke({
            "selected_keyword": state["selected_keyword"],
            "requirement_description": state["requirement_description"]
        })
        
        state["requirements_output"] = result
        state["messages"].append(SystemMessage(content=f"Requirements: {len(result.requirements)}"))
        logger.info(f"Generated {len(result.requirements)} requirements")
        
        for i, req in enumerate(result.requirements, 1):
            logger.debug(f"  Requirement {i}: {req[:80]}...")
        
        if state.get("regenerate_flag"):
            state["regenerate_flag"] = None
        
        return state
    except Exception as e:
        logger.error(f"Error generating requirements: {e}", exc_info=True)
        raise

def generate_risks(state: KeywordState) -> KeywordState:
    """Generate risks from requirements."""
    logger.info("Generating risks")
    
    # Format requirements for the prompt
    requirements_text = "\n".join([
        f"{i}. {req}" 
        for i, req in enumerate(state["requirements_output"].requirements, 1)
    ])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a risk analysis expert. You MUST respond with valid JSON in the exact format requested."),
        ("user", """Based on these requirements:

{requirements_text}

Generate exactly 5 risks (one corresponding to each requirement above). Each risk should:
- Be specific and realistic
- Describe the potential negative impact
- Be actionable for mitigation
- Be at least 2 sentences long

Respond with a JSON object in this EXACT format:
{{
  "Risks": [
    "Risk 1 corresponding to requirement 1...",
    "Risk 2 corresponding to requirement 2...",
    "Risk 3 corresponding to requirement 3...",
    "Risk 4 corresponding to requirement 4...",
    "Risk 5 corresponding to requirement 5..."
  ]
}}

Do not include any other text or explanation. Only return the JSON object.""")
    ])
    
    try:
        llm_structured = llm.with_structured_output(RisksOutput)
        result = (prompt | llm_structured).invoke({
            "requirements_text": requirements_text
        })
        
        state["risks_output"] = result
        state["messages"].append(SystemMessage(content=f"Risks: {len(result.Risks)}"))
        logger.info(f"Generated {len(result.Risks)} risks")
        
        for i, risk in enumerate(result.Risks, 1):
            logger.debug(f"  Risk {i}: {risk[:80]}...")
        
        if state.get("regenerate_flag"):
            state["regenerate_flag"] = None
        
        return state
    except Exception as e:
        logger.error(f"Error generating risks: {e}", exc_info=True)
        raise

def call_save_tool(state: KeywordState) -> KeywordState:
    """Save data to Neo4j."""
    logger.info("Saving to Neo4j")
    
    try:
        result = save_to_neo4j.invoke({
            "requirements": state["requirements_output"].requirements,
            "risks": state["risks_output"].Risks,
            "project_name": state["project_name"],
            "keyword": state["selected_keyword"]
        })
        
        state["messages"].append(SystemMessage(content=result))
        logger.info("Saved successfully")
        return state
    except Exception as e:
        logger.error(f"Save error: {e}", exc_info=True)
        raise