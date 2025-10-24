"""LangGraph tools for Neo4j operations."""
from langchain_core.tools import tool
from langchain_neo4j import Neo4jGraph
from typing import List,Dict,Annotated
from backend.config.config import settings
from backend.logger.logger import logger

# Initialize Neo4j - Make this accessible for direct queries
graph_db = Neo4jGraph(
    url=settings.neo4j_url,
    username=settings.neo4j_username,
    password=settings.neo4j_password,
    database=settings.neo4j_database,
    enhanced_schema=True
)

@tool
def save_to_neo4j(
    requirements: Annotated[List[str], "List of requirements"],
    risks: Annotated[List[str], "List of risks"],
    project_name: Annotated[str, "Project name"],
    keyword: Annotated[str, "Selected keyword"]
) -> str:
    """Save requirements and risks to Neo4j database."""
    try:
        logger.info(f"Saving to Neo4j: {project_name}")
        
        # Create Project
        graph_db.query("""
            MERGE (p:Project {name: $project_name})
            SET p.keyword = $keyword,
                p.updated_at = datetime()
            RETURN p
        """, {"project_name": project_name, "keyword": keyword})
        
        # Create Requirements
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
        
        # Create Risks
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
                RETURN rk
            """, {"desc": risk, "project_name": project_name, "idx": idx})
        
        logger.info(f"Saved {len(requirements)} requirements, {len(risks)} risks")
        return f"✅ Successfully saved to Neo4j"
    
    except Exception as e:
        logger.error(f"Neo4j error: {e}", exc_info=True)
        return f"❌ Error: {str(e)}"
    
# Add to tools.py
@tool
def save_test_cases_to_neo4j(
    requirement: Annotated[str, "Requirement description"],
    test_cases: Annotated[List[Dict], "List of test cases"],
    project_name: Annotated[str, "Project name"],
    requirement_index: Annotated[int, "Requirement index"]
) -> str:
    """Save test cases to Neo4j database with relationships."""
    try:
        logger.info(f"Saving test cases to Neo4j for requirement {requirement_index}")
        
        for test_case in test_cases:
            # Create TestCase node
            graph_db.query("""
                MATCH (p:Project {name: $project_name})
                MATCH (r:Requirement {project: $project_name, index: $req_index})
                MERGE (tc:TestCase {
                    test_id: $test_id,
                    project: $project_name,
                    requirement_index: $req_index
                })
                SET tc.description = $description,
                    tc.test_steps = $test_steps,
                    tc.expected_result = $expected_result,
                    tc.test_type = $test_type,
                    tc.created_at = datetime()
                MERGE (r)-[:VERIFIED_BY]->(tc)
                MERGE (tc)-[:VALIDATES]->(r)
                RETURN tc
            """, {
                "project_name": project_name,
                "req_index": requirement_index + 1,
                "test_id": test_case["test_id"],
                "description": test_case["description"],
                "test_steps": test_case["test_steps"],
                "expected_result": test_case["expected_result"],
                "test_type": test_case["test_type"]
            })
        
        logger.info(f"Saved {len(test_cases)} test cases for requirement {requirement_index}")
        return f"✅ Successfully saved {len(test_cases)} test cases to Neo4j"
    
    except Exception as e:
        logger.error(f"Neo4j test case error: {e}", exc_info=True)
        return f"❌ Error saving test cases: {str(e)}"