"""Project state management routes."""
from fastapi import APIRouter, HTTPException

from backend.model.models import ItemUpdateRequest, WorkflowResponse
from backend.logger.logger import logger
from api.shared.state import workflow_states

router = APIRouter()

@router.get("/list-all-projects")
async def list_projects():
    """List all projects."""
    return {
        "projects": list(workflow_states.keys()),
        "count": len(workflow_states)
    }

# @router.get("/{thread_id}", response_model=WorkflowResponse)

# async def get_project(thread_id: str):
#     """Get project status."""
#     try:
#         if thread_id not in workflow_states:
#             raise HTTPException(status_code=404, detail="Thread not found2")
        
#         state = workflow_states[thread_id]
        
#         return WorkflowResponse(
#             thread_id=thread_id,
#             status="active",
#             keywords=state["keyword_output"].keywords if state.get("keyword_output") else None,
#             selected_keyword=state.get("selected_keyword"),
#             requirements=state["requirements_output"].requirements if state.get("requirements_output") else None,
#             risks=state["risks_output"].Risks if state.get("risks_output") else None
#         )
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error getting project: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/")
# async def list_projects():
#     """List all projects."""
#     return {
#         "projects": list(workflow_states.keys()),
#         "count": len(workflow_states)
#     }


@router.post("/update-item", response_model=WorkflowResponse)
async def update_item(request: ItemUpdateRequest):
    """Manually update a requirement or risk."""
    try:
        thread_id = request.thread_id
        
        if thread_id not in workflow_states:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        state = workflow_states[thread_id]
        
        if request.type == "requirement":
            if not state.get("requirements_output") or request.index >= len(state["requirements_output"].requirements):
                raise HTTPException(status_code=400, detail="Invalid requirement index")
            
            # Update requirement
            state["requirements_output"].requirements[request.index] = request.new_content
            
            # Regenerate associated risk if requested
            if request.update_related and state.get("risks_output"):
                from backend.nodes.nodes import generate_risks
                state = generate_risks(state)
                
        elif request.type == "risk":
            if not state.get("risks_output") or request.index >= len(state["risks_output"].Risks):
                raise HTTPException(status_code=400, detail="Invalid risk index")
            
            # Update risk
            state["risks_output"].Risks[request.index] = request.new_content
        
        # Update stored state
        workflow_states[thread_id] = state
        
        return WorkflowResponse(
            thread_id=thread_id,
            status="updated",
            selected_keyword=state["selected_keyword"],
            requirements=state["requirements_output"].requirements if state.get("requirements_output") else None,
            risks=state["risks_output"].Risks if state.get("risks_output") else None,
            message=f"Updated {request.type} at index {request.index}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating item: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))