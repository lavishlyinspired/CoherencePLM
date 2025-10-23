"""LangGraph node definitions."""
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from langgraph.graph import MessagesState
from typing import Optional, List, Dict
import json
import re
from config import settings
from models import KeywordOutput, RequirementsOutput, RisksOutput
from logger import logger
from tools import save_to_neo4j

llm = ChatGroq(model=settings.llm_model)

class KeywordState(MessagesState):
    """State for workflow."""
    requirement_description: str
    keyword_output: Optional[KeywordOutput] = None
    selected_keyword: Optional[str] = None
    requirements_output: Optional[RequirementsOutput] = None
    risks_output: Optional[RisksOutput] = None
    project_name: str = "Default_Project"
    regenerate_flag: Optional[str] = None

def safe_json_parse(json_str: str, default=None):
    """Safely parse JSON with multiple fallback strategies."""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Try to fix common JSON issues
        try:
            # Remove extra commas
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)
            return json.loads(json_str)
        except:
            return default

def extract_json_from_text(text: str):
    """Extract JSON from text response."""
    # Try to find JSON in code blocks first
    if '```json' in text:
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            return match.group(1).strip()
    
    # Try to find JSON object
    if '{' in text and '}' in text:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            return text[start:end]
    
    # Try to find JSON array
    if '[' in text and ']' in text:
        start = text.find('[')
        end = text.rfind(']') + 1
        if start >= 0 and end > start:
            return text[start:end]
    
    return None

def generate_keywords(state: KeywordState) -> KeywordState:
    """Generate keywords from requirement description."""
    logger.info("Generating keywords")
    
    prompt = ChatPromptTemplate.from_template("""
    You are an expert requirement analyst.  
    Given this requirement description: "{requirement_description}"
    
    Generate exactly 5 keywords, each containing 3 words. 
    
    Return ONLY a JSON array of strings like this:
    ["keyword one two", "another three words", "more keywords here", "additional keyword set", "final three words"]
    
    Do not include any other text or explanation.
    """)
    
    try:
        # Use direct LLM call - NO structured output
        response = (prompt | llm).invoke({
            "requirement_description": state["requirement_description"]
        })
        
        content = response.content.strip()
        logger.info(f"Raw keywords response: {content}")
        
        # Extract and parse JSON
        json_str = extract_json_from_text(content)
        if json_str:
            keywords = safe_json_parse(json_str)
        else:
            # If no JSON found, try to parse as array directly
            if content.startswith('[') and content.endswith(']'):
                keywords = safe_json_parse(content)
            else:
                raise ValueError("No valid JSON found in response")
        
        # Validate and ensure we have 5 keywords
        if not keywords or not isinstance(keywords, list) or len(keywords) != 5:
            logger.warning(f"Invalid keywords format, using fallback. Got: {keywords}")
            keywords = [
                "advanced safety features",
                "fuel efficient engines", 
                "comfortable interior design",
                "advanced technology integration",
                "reliable performance standards"
            ]
        
        result = KeywordOutput(keywords=keywords)
        state["keyword_output"] = result
        state["messages"].append(SystemMessage(content=f"Keywords: {result.keywords}"))
        logger.info(f"Generated {len(result.keywords)} keywords")
        return state
        
    except Exception as e:
        logger.error(f"Error generating keywords: {e}")
        # Provide fallback keywords
        fallback_keywords = [
            "advanced safety features",
            "fuel efficient engines", 
            "comfortable interior design",
            "advanced technology integration",
            "reliable performance standards"
        ]
        state["keyword_output"] = KeywordOutput(keywords=fallback_keywords)
        state["messages"].append(SystemMessage(content=f"Fallback keywords: {fallback_keywords}"))
        return state

def generate_requirements(state: KeywordState) -> KeywordState:
    """Generate requirements from selected keyword."""
    logger.info(f"Generating requirements for: {state['selected_keyword']}")
    
    prompt = ChatPromptTemplate.from_template("""
    You are an expert requirement analyst.  
    Requirement description: "{requirement_description}"
    Selected keyword: "{selected_keyword}"
    
    Generate 5 formal requirements based on the keyword.
    
    Return ONLY a JSON array of strings like this:
    ["Requirement 1 description", "Requirement 2 description", "Requirement 3 description", "Requirement 4 description", "Requirement 5 description"]
    
    Do not include any other text or explanation.
    """)
    
    try:
        # Use direct LLM call - NO structured output
        response = (prompt | llm).invoke({
            "selected_keyword": state["selected_keyword"],
            "requirement_description": state["requirement_description"]
        })
        
        content = response.content.strip()
        logger.info(f"Raw requirements response: {content}")
        
        # Extract and parse JSON
        json_str = extract_json_from_text(content)
        if json_str:
            requirements = safe_json_parse(json_str)
        else:
            if content.startswith('[') and content.endswith(']'):
                requirements = safe_json_parse(content)
            else:
                raise ValueError("No valid JSON found in response")
        
        # Validate and ensure we have 5 requirements
        if not requirements or not isinstance(requirements, list) or len(requirements) != 5:
            logger.warning(f"Invalid requirements format, using fallback. Got: {requirements}")
            requirements = [
                f"The system shall implement {state['selected_keyword']} for optimal performance",
                f"The design shall incorporate {state['selected_keyword']} for user satisfaction",
                f"The product shall maintain {state['selected_keyword']} throughout its lifecycle",
                f"The implementation shall ensure {state['selected_keyword']} meets industry standards",
                f"The solution shall provide {state['selected_keyword']} with minimal maintenance"
            ]
        
        result = RequirementsOutput(requirements=requirements)
        state["requirements_output"] = result
        state["messages"].append(SystemMessage(content=f"Requirements: {len(result.requirements)}"))
        logger.info(f"Generated {len(result.requirements)} requirements")
        
        if state.get("regenerate_flag"):
            state["regenerate_flag"] = None
        
        return state
        
    except Exception as e:
        logger.error(f"Error generating requirements: {e}")
        # Provide fallback requirements
        fallback_requirements = [
            f"The system shall implement {state['selected_keyword']} for optimal performance",
            f"The design shall incorporate {state['selected_keyword']} for user satisfaction",
            f"The product shall maintain {state['selected_keyword']} throughout its lifecycle",
            f"The implementation shall ensure {state['selected_keyword']} meets industry standards",
            f"The solution shall provide {state['selected_keyword']} with minimal maintenance"
        ]
        state["requirements_output"] = RequirementsOutput(requirements=fallback_requirements)
        return state

def generate_risks(state: KeywordState) -> KeywordState:
    """Generate risks from requirements."""
    logger.info("Generating risks")
    
    prompt = ChatPromptTemplate.from_template("""
    You are a risk analysis expert. 
    Based on these requirements:
    {requirements}
    
    Generate exactly 5 risks (one per requirement).
    
    Return ONLY a JSON object with a "Risks" key containing an array, like this:
    {{
      "Risks": [
        "Risk 1 description",
        "Risk 2 description",
        "Risk 3 description", 
        "Risk 4 description",
        "Risk 5 description"
      ]
    }}
    
    Do not include any other text or explanation.
    """)
    
    try:
        requirements = state["requirements_output"].requirements
        
        # Use direct LLM call - NO structured output
        response = (prompt | llm).invoke({
            "requirements": requirements
        })
        
        content = response.content.strip()
        logger.info(f"Raw risks response: {content}")
        
        # Extract and parse JSON
        json_str = extract_json_from_text(content)
        if json_str:
            risks_data = safe_json_parse(json_str)
        else:
            if content.startswith('{') and content.endswith('}'):
                risks_data = safe_json_parse(content)
            else:
                raise ValueError("No valid JSON found in response")
        
        # Extract risks from the parsed data
        if risks_data and isinstance(risks_data, dict) and "Risks" in risks_data:
            risks = risks_data["Risks"]
        else:
            risks = []
        
        # Validate and ensure we have 5 risks
        if not risks or not isinstance(risks, list) or len(risks) != 5:
            logger.warning(f"Invalid risks format, using fallback. Got: {risks}")
            risks = generate_fallback_risks(requirements)
        
        result = RisksOutput(Risks=risks)
        state["risks_output"] = result
        state["messages"].append(SystemMessage(content=f"Risks: {len(result.Risks)}"))
        logger.info(f"Generated {len(result.Risks)} risks")
        
        if state.get("regenerate_flag"):
            state["regenerate_flag"] = None
        
        return state
        
    except Exception as e:
        logger.error(f"Error generating risks: {e}")
        # Provide fallback risks
        fallback_risks = generate_fallback_risks(state["requirements_output"].requirements)
        state["risks_output"] = RisksOutput(Risks=fallback_risks)
        return state

def generate_fallback_risks(requirements):
    """Generate fallback risks when LLM fails."""
    fallback_risks = []
    for i, req in enumerate(requirements):
        fallback_risks.append(f"Potential challenges in implementing: {req[:60]}...")
    
    # Ensure we have exactly 5 risks
    while len(fallback_risks) < 5:
        fallback_risks.append(f"General implementation risk for requirement {len(fallback_risks) + 1}")
    
    return fallback_risks[:5]

def generate_single_requirement_with_feedback(state: KeywordState, index: int, feedback: str) -> str:
    """Generate a single requirement with user feedback for a specific index."""
    logger.info(f"🔧 [NODES] Generating single requirement at index {index} with feedback: {feedback}")
    
    try:
        current_reqs = state["requirements_output"].requirements
        current_requirement = current_reqs[index] if index < len(current_reqs) else ""
        
        logger.info(f"🔧 [NODES] Current requirement at index {index}: '{current_requirement}'")
        
        prompt = ChatPromptTemplate.from_template("""
        You are an expert requirement analyst.  
        Original requirement description: "{requirement_description}"
        Selected keyword: "{selected_keyword}"
        
        Current requirement that needs improvement (at position {index}):
        "{current_requirement}"
        
        User feedback: "{feedback}"
        
        Please regenerate ONLY this specific requirement, incorporating the user's feedback.
        Keep the same formal requirement style and maintain consistency with the other requirements.
        
        Return ONLY the new requirement text, nothing else.
        """)
        
        # Use direct LLM call
        response = (prompt | llm).invoke({
            "selected_keyword": state["selected_keyword"],
            "requirement_description": state["requirement_description"],
            "current_requirement": current_requirement,
            "feedback": feedback,
            "index": index + 1  # Show 1-based index to user
        })
        
        content = response.content.strip()
        logger.info(f"🔧 [NODES] Raw single requirement response: '{content}'")
        
        # Clean the response - remove quotes if present
        cleaned_content = content.strip('"').strip("'").strip()
        
        # Validate that we got a reasonable requirement
        if len(cleaned_content) < 10:  # Too short to be a real requirement
            logger.warning(f"🔧 [NODES] Generated requirement too short, using original: '{cleaned_content}'")
            return current_requirement
        
        logger.info(f"🔧 [NODES] Successfully generated new requirement for index {index}: '{cleaned_content}'")
        return cleaned_content
        
    except Exception as e:
        logger.error(f"🔧 [NODES] Error generating single requirement with feedback: {e}")
        # Return the original requirement if generation fails
        return state["requirements_output"].requirements[index] if index < len(state["requirements_output"].requirements) else ""

def generate_single_risk_with_feedback(state: KeywordState, index: int, feedback: str) -> str:
    """Generate a single risk with user feedback for a specific index."""
    logger.info(f"🔧 [NODES] Generating single risk at index {index} with feedback: {feedback}")
    
    try:
        current_risks = state["risks_output"].Risks
        current_risk = current_risks[index] if index < len(current_risks) else ""
        current_requirement = state["requirements_output"].requirements[index] if index < len(state["requirements_output"].requirements) else ""
        
        logger.info(f"🔧 [NODES] Current risk at index {index}: '{current_risk}'")
        logger.info(f"🔧 [NODES] Associated requirement: '{current_requirement}'")
        
        prompt = ChatPromptTemplate.from_template("""
        You are a risk analysis expert. 
        Current requirement for this risk:
        "{current_requirement}"
        
        Current risk that needs improvement (at position {index}):
        "{current_risk}"
        
        User feedback: "{feedback}"
        
        Please regenerate ONLY this specific risk, incorporating the user's feedback.
        Keep the same risk analysis style and maintain consistency with the other risks.
        
        Return ONLY the new risk text, nothing else.
        """)
        
        # Use direct LLM call
        response = (prompt | llm).invoke({
            "current_requirement": current_requirement,
            "current_risk": current_risk,
            "feedback": feedback,
            "index": index + 1  # Show 1-based index to user
        })
        
        content = response.content.strip()
        logger.info(f"🔧 [NODES] Raw single risk response: '{content}'")
        
        # Clean the response - remove quotes if present
        cleaned_content = content.strip('"').strip("'").strip()
        
        # Validate that we got a reasonable risk
        if len(cleaned_content) < 10:  # Too short to be a real risk
            logger.warning(f"🔧 [NODES] Generated risk too short, using original: '{cleaned_content}'")
            return current_risk
        
        logger.info(f"🔧 [NODES] Successfully generated new risk for index {index}: '{cleaned_content}'")
        return cleaned_content
        
    except Exception as e:
        logger.error(f"🔧 [NODES] Error generating single risk with feedback: {e}")
        # Return the original risk if generation fails
        return state["risks_output"].Risks[index] if index < len(state["risks_output"].Risks) else ""

def generate_requirements_with_feedback(state: KeywordState, indexes: List[int], feedback: str) -> KeywordState:
    """Generate requirements with user feedback for specific indexes."""
    logger.info(f"Generating requirements with feedback for indexes: {indexes}")
    
    # Use the single requirement approach for each index
    current_requirements = state["requirements_output"].requirements.copy()
    
    for idx in indexes:
        if idx < len(current_requirements):
            updated_requirement = generate_single_requirement_with_feedback(state, idx, feedback)
            if updated_requirement:
                current_requirements[idx] = updated_requirement
    
    state["requirements_output"].requirements = current_requirements
    state["messages"].append(SystemMessage(
        content=f"Regenerated requirements with feedback for indexes {indexes}"
    ))
    logger.info(f"Updated {len(indexes)} requirements with feedback")
    
    return state

def generate_risks_with_feedback(state: KeywordState, indexes: List[int], feedback: str) -> KeywordState:
    """Generate risks with user feedback for specific indexes."""
    logger.info(f"Generating risks with feedback for indexes: {indexes}")
    
    # Use the single risk approach for each index
    current_risks = state["risks_output"].Risks.copy()
    
    for idx in indexes:
        if idx < len(current_risks):
            updated_risk = generate_single_risk_with_feedback(state, idx, feedback)
            if updated_risk:
                current_risks[idx] = updated_risk
    
    state["risks_output"].Risks = current_risks
    state["messages"].append(SystemMessage(
        content=f"Regenerated risks with feedback for indexes {indexes}"
    ))
    logger.info(f"Updated {len(indexes)} risks with feedback")
    
    return state

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
        logger.error(f"Save error: {e}")
        raise
# Add to nodes.py
def generate_test_cases(state: KeywordState, requirement_index: int) -> KeywordState:
    """Generate test cases for a specific requirement."""
    logger.info(f"Generating test cases for requirement index: {requirement_index}")
    
    if not state.get("requirements_output") or requirement_index >= len(state["requirements_output"].requirements):
        logger.error(f"Invalid requirement index: {requirement_index}")
        return state
    
    requirement = state["requirements_output"].requirements[requirement_index]
    
    prompt = ChatPromptTemplate.from_template("""
    You are a quality assurance expert.
    Requirement: "{requirement}"
    
    Generate 2-3 comprehensive test cases for this requirement. Each test case should have:
    - A unique test case ID (format: TC_REQ{index}_001, TC_REQ{index}_002, etc.)
    - Test case description
    - Test steps
    - Expected result
    - Test type (Functional, Integration, System, etc.)
    
    Return ONLY a JSON array of objects like this:
    [
      {{
        "test_id": "TC_REQ{index}_001",
        "description": "Test case description",
        "test_steps": ["Step 1", "Step 2", "Step 3"],
        "expected_result": "Expected outcome",
        "test_type": "Functional"
      }},
      {{
        "test_id": "TC_REQ{index}_002", 
        "description": "Another test case description",
        "test_steps": ["Step 1", "Step 2"],
        "expected_result": "Expected outcome",
        "test_type": "Integration"
      }}
    ]
    
    Generate exactly 2-3 test cases. Do not include any other text or explanation.
    """)
    
    try:
        response = (prompt | llm).invoke({
            "requirement": requirement,
            "index": requirement_index + 1
        })
        
        content = response.content.strip()
        logger.info(f"Raw test cases response: {content}")
        
        # Extract and parse JSON
        json_str = extract_json_from_text(content)
        if json_str:
            test_cases = safe_json_parse(json_str)
        else:
            if content.startswith('[') and content.endswith(']'):
                test_cases = safe_json_parse(content)
            else:
                raise ValueError("No valid JSON found in response")
        
        # Validate test cases
        if not test_cases or not isinstance(test_cases, list) or len(test_cases) < 2:
            logger.warning(f"Invalid test cases format, using fallback. Got: {test_cases}")
            test_cases = generate_fallback_test_cases(requirement, requirement_index)
        
        # Initialize test_cases_output if it doesn't exist
        if "test_cases_output" not in state:
            state["test_cases_output"] = {}
        
        # Store test cases for this requirement
        state["test_cases_output"][requirement_index] = test_cases
        state["messages"].append(SystemMessage(
            content=f"Generated {len(test_cases)} test cases for requirement {requirement_index + 1}"
        ))
        logger.info(f"Generated {len(test_cases)} test cases for requirement {requirement_index}")
        
        return state
        
    except Exception as e:
        logger.error(f"Error generating test cases: {e}")
        # Provide fallback test cases
        fallback_test_cases = generate_fallback_test_cases(requirement, requirement_index)
        if "test_cases_output" not in state:
            state["test_cases_output"] = {}
        state["test_cases_output"][requirement_index] = fallback_test_cases
        return state

def generate_fallback_test_cases(requirement, requirement_index):
    """Generate fallback test cases when LLM fails."""
    base_id = f"TC_REQ{requirement_index + 1}"
    return [
        {
            "test_id": f"{base_id}_001",
            "description": f"Basic functionality test for: {requirement[:50]}...",
            "test_steps": [
                "Set up test environment",
                "Execute main functionality",
                "Verify results"
            ],
            "expected_result": "Functionality works as specified",
            "test_type": "Functional"
        },
        {
            "test_id": f"{base_id}_002",
            "description": f"Integration test for: {requirement[:50]}...",
            "test_steps": [
                "Set up integrated environment",
                "Execute with dependent components",
                "Verify integration points"
            ],
            "expected_result": "Integration works correctly",
            "test_type": "Integration"
        }
    ]
# Test function
def test_single_requirement_function():
    """Test function to verify the single requirement function exists."""
    logger.info("🔧 [TEST] test_single_requirement_function called successfully!")
    return "Test requirement"


# Add this to your existing tools or nodes file
def enhance_save_with_traceability(project_name: str, requirements: List[str], risks: List[str], test_cases: Optional[Dict] = None):
    """
    Enhanced save function that creates traceability relationships
    """
    try:
        # Your existing save logic here...
        
        # Additional: Create traceability relationships
        for i, (req, risk) in enumerate(zip(requirements, risks)):
            req_id = f"REQ_{project_name}_{i+1}"
            risk_id = f"RISK_{project_name}_{i+1}"
            
            # Create HAS_RISK relationship
            graph_db.query("""
                MATCH (r:Requirement {id: $req_id})
                MATCH (rk:Risk {id: $risk_id})
                MERGE (r)-[:HAS_RISK]->(rk)
            """, {"req_id": req_id, "risk_id": risk_id})
            
            # Create test case relationships if available
            if test_cases and i in test_cases:
                for j, test_case in enumerate(test_cases[i]):
                    tc_id = f"TC_{project_name}_{i+1}_{j+1}"
                    graph_db.query("""
                        MATCH (r:Requirement {id: $req_id})
                        MATCH (tc:TestCase {id: $tc_id})
                        MERGE (r)-[:VERIFIED_BY]->(tc)
                    """, {"req_id": req_id, "tc_id": tc_id})
        
        return f"Enhanced save completed with traceability for {len(requirements)} requirements"
    
    except Exception as e:
        logger.error(f"Error in enhanced save: {e}")
        raise