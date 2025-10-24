"""Project saving routes."""
from fastapi import APIRouter, HTTPException

from backend.model.models import SelectiveSaveRequest
from backend.logger.logger import logger
from backend.tools.tools import save_to_neo4j
from api.shared.state import workflow_states

router = APIRouter()

@router.post("/save-selected")
async def save_selected_requirements(request: SelectiveSaveRequest):
    """Save only selected requirements to Neo4j."""
    try:
        thread_id = request.thread_id
        
        if thread_id not in workflow_states:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        state = workflow_states[thread_id]
        
        if not request.requirements or not request.risks:
            raise HTTPException(status_code=400, detail="No requirements or risks provided")
        
        if len(request.requirements) != len(request.risks):
            raise HTTPException(status_code=400, detail="Requirements and risks count mismatch")
        
        logger.info(f"Saving {len(request.requirements)} selected requirements to Neo4j")
        
        # Save selected requirements to Neo4j
        result = save_to_neo4j.invoke({
            "requirements": request.requirements,
            "risks": request.risks,
            "project_name": thread_id,
            "keyword": request.keyword
        })
        
        # Update messages in state
        state["messages"].append(f"Selected requirements saved: {result}")
        
        # Update stored state
        workflow_states[thread_id] = state
        
        return {
            "thread_id": thread_id,
            "status": "saved",
            "saved_count": len(request.requirements),
            "message": f"Successfully saved {len(request.requirements)} requirements to Neo4j"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving selected requirements: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/save")
async def save_project(thread_id: str):
    """Save project to Neo4j."""
    try:
        if thread_id not in workflow_states:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        state = workflow_states[thread_id]
        
        if not state.get("requirements_output") or not state.get("risks_output"):
            raise HTTPException(status_code=400, detail="Generate requirements/risks first")
        
        logger.info(f"Saving project {thread_id}")
        
        # Call save tool directly
        from backend.nodes.nodes import call_save_tool
        state = call_save_tool(state)
        
        # Update stored state
        workflow_states[thread_id] = state
        
        return {
            "thread_id": thread_id,
            "status": "saved",
            "message": "Saved to Neo4j successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))