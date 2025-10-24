"""Neo4j-specific operations routes."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from backend.logger.logger import logger
from backend.tools.tools import graph_db
from backend.model.models import ItemUpdateRequest, WorkflowResponse
from api.shared.state import workflow_states

router = APIRouter()

@router.get("/risks-from-neo4j")
async def get_risks_from_neo4j(project_name: str = Query(...), risk_indexes: str = Query(None)):
    """Get only risks from Neo4j for a project."""
    try:
        # Query Neo4j for risks only
        result = graph_db.query("""
            MATCH (p:Project {name: $name})-[:HAS_REQUIREMENT]->(r:Requirement)
            MATCH (r)-[:HAS_RISK]->(rk:Risk)
            RETURN r.index AS req_index, r.description AS requirement,
                   rk.index AS risk_index, rk.description AS risk
            ORDER BY req_index, risk_index
        """, {"name": project_name})

        if not result:
            raise HTTPException(status_code=404, detail="Project not found in Neo4j")

        # Extract just the risk descriptions
        risks = []
        for record in result:
            if record["risk"]:
                risks.append(record["risk"])

        return {
            "risks": risks,
            "count": len(risks),
            "message": f"Found {len(risks)} risks for project {project_name}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching risks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search-risks")
async def search_risks(query: str):
    """Search risks in Neo4j database."""
    try:
        from backend.tools.tools import graph_db
        
        result = graph_db.query("""
            MATCH (rk:Risk)
            WHERE toLower(rk.description) CONTAINS toLower($query)
            RETURN rk.description AS risk, 
                   rk.project AS project,
                   rk.index AS index
            ORDER BY rk.project, rk.index
        """, {"query": query})
        print("result is ", result)
        risks = []
        for record in result:
            risks.append({
                "description": record["risk"],
                "project": record.get("project", "Unknown"),
                "index": record.get("index", 0)
            })
        
        return risks
    except Exception as e:
        logger.error(f"Error searching risks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/load-from-neo4j")
async def load_project_from_neo4j(project_name: str = Query(...)):
    """
    Load a project from Neo4j into memory and return requirements + risks,
    associating each risk with its requirement.
    """
    try:
        from backend.tools.tools import graph_db
        from backend.model.models import RequirementsOutput, RisksOutput
        
        # Query Neo4j for project keyword first
        project_result = graph_db.query("""
            MATCH (p:Project {name: $name})
            RETURN p.keyword AS keyword
        """, {"name": project_name})
        
        keyword = project_result[0]["keyword"] if project_result and len(project_result) > 0 else project_name
        
        logger.info(f"Loading project {project_name} with keyword: {keyword}")
        
        # Query Neo4j for requirements + risks
        result = graph_db.query("""
            MATCH (p:Project {name: $name})-[:HAS_REQUIREMENT]->(r:Requirement)
            OPTIONAL MATCH (r)-[:HAS_RISK]->(rk:Risk)
            RETURN r.index AS req_index, r.description AS requirement,
                   rk.index AS risk_index, rk.description AS risk
            ORDER BY req_index, risk_index
        """, {"name": project_name})

        if not result:
            raise HTTPException(status_code=404, detail="Project not found in Neo4j")

        # Store unique requirements by index
        requirements = {}
        risks = []

        for record in result:
            req_index = record["req_index"]
            if req_index not in requirements:
                requirements[req_index] = record["requirement"]

            risk_desc = record["risk"]
            if risk_desc:
                risks.append({
                    "description": risk_desc,
                    "requirement_index": req_index,
                    "requirement": requirements[req_index]
                })

        # Create proper state structure matching what regenerate expects
        state = {
            "project_name": project_name,
            "requirement_description": f"Loaded project: {project_name}",
            "messages": [],
            "keyword_output": None,
            "selected_keyword": keyword,
            "requirements_output": RequirementsOutput(
                requirements=[requirements[i] for i in sorted(requirements.keys())]
            ),
            "risks_output": RisksOutput(
                Risks=[risk["description"] for risk in risks]
            ),
            "regenerate_flag": None
        }

        # Store in workflow_states so it can be used for regeneration
        workflow_states[project_name] = state
        
        logger.info(f"Stored state for {project_name} with {len(state['requirements_output'].requirements)} requirements")

        return {
            "thread_id": project_name,
            "status": "loaded",
            "selected_keyword": keyword,
            "requirements": state["requirements_output"].requirements,
            "risks": [risk["description"] for risk in risks],
            "risks_with_requirements": risks,
            "message": f"Loaded project {project_name} into memory"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))