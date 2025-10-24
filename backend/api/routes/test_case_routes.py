"""Test case-related API routes."""
from fastapi import APIRouter, HTTPException
from backend.model.models import TestCaseRequest, TestCaseUpdateRequest, WorkflowResponse
from backend.logger.logger import logger
from backend.tools.tools import save_test_cases_to_neo4j

router = APIRouter()

# This would be imported from main.py or a shared state module
from api.shared.state import workflow_states

@router.post("/generate-test-cases", response_model=WorkflowResponse)
async def generate_test_cases(request: TestCaseRequest):
    """Generate test cases for a specific requirement."""
    try:
        thread_id = request.thread_id
        
        if thread_id not in workflow_states:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        state = workflow_states[thread_id]
        
        if not state.get("requirements_output"):
            raise HTTPException(status_code=400, detail="No requirements available")
        
        logger.info(f"Generating test cases for requirement {request.requirement_index}")
        
        from backend.nodes.nodes import generate_test_cases
        state = generate_test_cases(state, request.requirement_index)
        
        # Update stored state
        workflow_states[thread_id] = state
        
        return WorkflowResponse(
            thread_id=thread_id,
            status="test_cases_generated",
            selected_keyword=state["selected_keyword"],
            requirements=state["requirements_output"].requirements if state.get("requirements_output") else None,
            risks=state["risks_output"].Risks if state.get("risks_output") else None,
            message=f"Generated test cases for requirement {request.requirement_index + 1}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating test cases: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/save-test-cases")
async def save_test_cases(request: TestCaseUpdateRequest):
    """Save test cases to Neo4j."""
    try:
        thread_id = request.thread_id
        
        if thread_id not in workflow_states:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        state = workflow_states[thread_id]
        
        if not state.get("requirements_output") or request.requirement_index >= len(state["requirements_output"].requirements):
            raise HTTPException(status_code=400, detail="Invalid requirement index")
        
        requirement = state["requirements_output"].requirements[request.requirement_index]
        
        logger.info(f"Saving {len(request.test_cases)} test cases to Neo4j")
        
        result = save_test_cases_to_neo4j.invoke({
            "requirement": requirement,
            "test_cases": request.test_cases,
            "project_name": thread_id,
            "requirement_index": request.requirement_index
        })
        
        # Update state if test cases exist in memory
        if state.get("test_cases_output") and request.requirement_index in state["test_cases_output"]:
            state["test_cases_output"][request.requirement_index] = request.test_cases
        
        # Update stored state
        workflow_states[thread_id] = state
        
        return {
            "thread_id": thread_id,
            "status": "saved",
            "saved_count": len(request.test_cases),
            "message": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving test cases: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-cases/{thread_id}/{requirement_index}")
async def get_test_cases(thread_id: str, requirement_index: int):
    """Get test cases for a specific requirement."""
    try:
        if thread_id not in workflow_states:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        state = workflow_states[thread_id]
        
        test_cases = []
        if state.get("test_cases_output") and requirement_index in state["test_cases_output"]:
            test_cases = state["test_cases_output"][requirement_index]
        
        return {
            "thread_id": thread_id,
            "requirement_index": requirement_index,
            "test_cases": test_cases,
            "count": len(test_cases)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting test cases: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))