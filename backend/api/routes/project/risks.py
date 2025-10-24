"""Risk management routes."""
from fastapi import APIRouter, HTTPException

from backend.model.models import RiskUpdateRequest
from backend.logger.logger import logger
from backend.tools.tools import graph_db
from api.shared.state import workflow_states

router = APIRouter()

@router.post("/update-risks")
async def update_risks(request: RiskUpdateRequest):
    """Update specific risks in Neo4j."""
    try:
        thread_id = request.thread_id
        
        if thread_id not in workflow_states:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        state = workflow_states[thread_id]
        
        if not request.risk_data:
            raise HTTPException(status_code=400, detail="No risk data provided")
        
        logger.info(f"Updating {len(request.risk_data)} risks in Neo4j")
        
        # Update risks in Neo4j
        from backend.tools.tools import graph_db
        
        updated_count = 0
        for risk_item in request.risk_data:
            risk = risk_item.get("risk")
            requirement_index = risk_item.get("requirement_index")
            requirement = risk_item.get("requirement")
            
            if risk and requirement_index is not None:
                # Update the risk in Neo4j
                graph_db.query("""
                    MATCH (p:Project {name: $project_name})
                    MATCH (r:Requirement {project: $project_name, index: $req_index})
                    MATCH (r)-[:HAS_RISK]->(rk:Risk {project: $project_name, index: $risk_index})
                    SET rk.description = $risk_description
                    RETURN rk
                """, {
                    "project_name": thread_id,
                    "req_index": requirement_index + 1,  # Convert to 1-based index
                    "risk_index": requirement_index + 1,
                    "risk_description": risk
                })
                updated_count += 1
        
        # Update state risks if they exist in memory
        if state.get("risks_output") and state["risks_output"].Risks:
            for risk_item in request.risk_data:
                idx = risk_item.get("requirement_index")
                risk = risk_item.get("risk")
                if idx is not None and idx < len(state["risks_output"].Risks):
                    state["risks_output"].Risks[idx] = risk
        
        # Update stored state
        workflow_states[thread_id] = state
        
        return {
            "thread_id": thread_id,
            "status": "updated",
            "updated_count": updated_count,
            "message": f"Successfully updated {updated_count} risks in Neo4j"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating risks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-single-risk")
async def update_single_risk(request: dict):
    """Update a single risk in Neo4j."""
    try:
        thread_id = request.get("thread_id")
        risk_index = request.get("risk_index")
        risk = request.get("risk")
        requirement = request.get("requirement")
        
        if not thread_id or risk_index is None or not risk:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        if thread_id not in workflow_states:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        state = workflow_states[thread_id]
        
        logger.info(f"Updating risk at index {risk_index} in Neo4j")
        
        # Update the single risk in Neo4j
        from backend.tools.tools import graph_db
        
        graph_db.query("""
            MATCH (p:Project {name: $project_name})
            MATCH (r:Requirement {project: $project_name, index: $req_index})
            MATCH (r)-[:HAS_RISK]->(rk:Risk {project: $project_name, index: $risk_index})
            SET rk.description = $risk_description
            RETURN rk
        """, {
            "project_name": thread_id,
            "req_index": risk_index + 1,  # Convert to 1-based index
            "risk_index": risk_index + 1,
            "risk_description": risk
        })
        
        # Update state risk if it exists in memory
        if state.get("risks_output") and state["risks_output"].Risks and risk_index < len(state["risks_output"].Risks):
            state["risks_output"].Risks[risk_index] = risk
        
        # Update stored state
        workflow_states[thread_id] = state
        
        return {
            "thread_id": thread_id,
            "status": "updated",
            "risk_index": risk_index,
            "message": "Risk updated successfully in Neo4j"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating single risk: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))