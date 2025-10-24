"""Project creation and keyword selection routes."""
from fastapi import APIRouter, HTTPException
import uuid

from backend.config.config import settings
from backend.model.models import ProjectRequest, KeywordSelectionRequest, WorkflowResponse
from backend.workflow.graph import workflow_graph
from backend.logger.logger import logger
from api.shared.state import workflow_states

router = APIRouter()

@router.post("/create", response_model=WorkflowResponse)
async def create_project(request: ProjectRequest):
    """Create project and generate keywords."""
    try:
        thread_id = request.project_name or f"project_{uuid.uuid4().hex[:8]}"
        logger.info(f"Creating project: {thread_id}")
        
        state = {
            "requirement_description": request.requirement_description,
            "messages": [],
            "keyword_output": None,
            "selected_keyword": None,
            "requirements_output": None,
            "risks_output": None,
            "project_name": thread_id,
            "regenerate_flag": None
        }
        
        thread = {"configurable": {"thread_id": thread_id}}
        result_state = None
        
        # Stream and get final state
        for event in workflow_graph.stream(state, thread, stream_mode="values"):
            result_state = event
            logger.debug(f"Event: {event.keys()}")
        
        # Store final state
        workflow_states[thread_id] = result_state
        
        keywords = None
        if result_state and result_state.get("keyword_output"):
            keywords = result_state["keyword_output"].keywords
        
        return WorkflowResponse(
            thread_id=thread_id,
            status="keywords_generated",
            keywords=keywords,
            message="Keywords generated. Select one to continue."
        )
    except Exception as e:
        logger.error(f"Error creating project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/select-keyword", response_model=WorkflowResponse)
async def select_keyword(request: KeywordSelectionRequest):
    """Select keyword and generate requirements/risks."""
    try:
        thread_id = request.thread_id
        
        if thread_id not in workflow_states:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        state = workflow_states[thread_id]
        
        if not state.get("keyword_output"):
            raise HTTPException(status_code=400, detail="No keywords available")
        
        keywords = state["keyword_output"].keywords
        if request.keyword_index >= len(keywords):
            raise HTTPException(status_code=400, detail="Invalid keyword index")
        
        # Select keyword
        selected_keyword = keywords[request.keyword_index]
        state["selected_keyword"] = selected_keyword
        
        logger.info(f"Selected keyword: {selected_keyword}")
        
        # Import locally
        from backend.nodes.nodes import generate_requirements, generate_risks
        
        # Generate requirements directly
        logger.info("Invoking generate_requirements")
        state = generate_requirements(state)
        
        # Try to generate risks, but continue even if it fails
        try:
            logger.info("Invoking generate_risks")
            state = generate_risks(state)
            risks_available = True
        except Exception as risk_error:
            logger.error(f"Risk generation failed but continuing: {risk_error}")
            risks_available = False
            # Set empty risks so the frontend doesn't crash
            from backend.model.models import RisksOutput
            state["risks_output"] = RisksOutput(Risks=["Risk generation failed"] * 5)
        
        # Update stored state
        workflow_states[thread_id] = state
        
        return WorkflowResponse(
            thread_id=thread_id,
            status="generated",
            selected_keyword=selected_keyword,
            requirements=state["requirements_output"].requirements if state.get("requirements_output") else None,
            risks=state["risks_output"].Risks if state.get("risks_output") else None,
            message="Requirements and risks generated" if risks_available else "Requirements generated (risks failed)"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error selecting keyword: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    

