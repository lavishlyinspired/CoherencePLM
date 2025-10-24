"""Project regeneration routes."""
from fastapi import APIRouter, HTTPException
from typing import List

from backend.model.models import RegenerateRequest, FeedbackRequest, SelectiveRegenerateRequest, WorkflowResponse
from backend.logger.logger import logger
from api.dependencies import safe_log_message
from api.shared.state import workflow_states

router = APIRouter()

@router.post("/regenerate", response_model=WorkflowResponse)
async def regenerate(request: RegenerateRequest):
    """Regenerate requirements, risks, or both."""
    try:
        thread_id = request.thread_id
        
        if thread_id not in workflow_states:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        state = workflow_states[thread_id]
        
        if not state.get("selected_keyword"):
            raise HTTPException(status_code=400, detail="No keyword selected")
        
        logger.info(f"Regenerating {request.regenerate_type}")
        
        from backend.nodes.nodes import generate_requirements, generate_risks
        
        # Regenerate based on type
        if request.regenerate_type in ["requirements", "both"]:
            logger.info("Regenerating requirements")
            state = generate_requirements(state)
        
        if request.regenerate_type in ["risks", "both"]:
            logger.info("Regenerating risks")
            state = generate_risks(state)
        
        # Update stored state
        workflow_states[thread_id] = state
        
        return WorkflowResponse(
            thread_id=thread_id,
            status="regenerated",
            selected_keyword=state["selected_keyword"],
            requirements=state["requirements_output"].requirements if state.get("requirements_output") else None,
            risks=state["risks_output"].Risks if state.get("risks_output") else None,
            message=f"Regenerated {request.regenerate_type}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/regenerate-with-feedback", response_model=WorkflowResponse)
async def regenerate_with_feedback(request: FeedbackRequest):
    """Regenerate specific requirements or risks with user feedback."""
    try:
        thread_id = request.thread_id
        
        if thread_id not in workflow_states:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        state = workflow_states[thread_id]
        
        # REMOVED STRICT CHECK - Allow missing keyword and use thread_id as fallback
        if not state.get("selected_keyword"):
            logger.warning(f"⚠️ No keyword selected for {thread_id}, using thread_id as fallback")
            state["selected_keyword"] = thread_id
        
        # Use safe logging
        safe_feedback = safe_log_message(request.feedback)
        logger.info(f"🔧 [API] Regenerating {request.regenerate_type} with feedback: {safe_feedback}")
        logger.info(f"🔧 [API] Indexes to update: {request.indexes}")
        
        # Import inside the function to avoid circular imports
        from backend.nodes.nodes import (
            generate_requirements, 
            generate_risks,
            generate_single_requirement_with_feedback,
            generate_single_risk_with_feedback
        )
        
        logger.info(f"🔧 [API] Successfully imported functions from nodes")
        
        if request.regenerate_type == "requirement":
            if not state.get("requirements_output"):
                raise HTTPException(status_code=400, detail="No requirements available")
            
            # Store current requirements and risks
            current_requirements = state["requirements_output"].requirements.copy()
            current_risks = state["risks_output"].Risks.copy() if state.get("risks_output") else []
            
            logger.info(f"🔧 [API] Current requirements before regeneration: {current_requirements}")
            logger.info(f"🔧 [API] Current risks before regeneration: {current_risks}")
            
            # Generate new requirements with feedback - but only for the specific indexes
            updated_requirement_indexes = []
            for idx in request.indexes:
                if idx < len(current_requirements):
                    logger.info(f"🔧 [API] Calling generate_single_requirement_with_feedback for index {idx}")
                    try:
                        updated_requirement = generate_single_requirement_with_feedback(
                            state, idx, request.feedback
                        )
                        logger.info(f"🔧 [API] Returned from generate_single_requirement_with_feedback: '{updated_requirement}'")
                        
                        if updated_requirement and updated_requirement != current_requirements[idx]:
                            current_requirements[idx] = updated_requirement
                            updated_requirement_indexes.append(idx)
                            logger.info(f"✅ [API] Updated requirement at index {idx}: '{updated_requirement}'")
                        else:
                            logger.warning(f"⚠️ [API] No change for requirement at index {idx}")
                    except Exception as e:
                        logger.error(f"❌ [API] Error updating requirement at index {idx}: {e}")
            
            # Update the state with only the changed requirements
            state["requirements_output"].requirements = current_requirements
            
            logger.info(f"🔧 [API] Final requirements after selective update: {state['requirements_output'].requirements}")
            logger.info(f"🔧 [API] Successfully updated {len(updated_requirement_indexes)} requirements")
            
            # Only regenerate specific risks for the updated requirements
            if updated_requirement_indexes:
                logger.info(f"🔧 [API] Regenerating risks only for updated requirement indexes: {updated_requirement_indexes}")
                for req_idx in updated_requirement_indexes:
                    if req_idx < len(current_risks):
                        logger.info(f"🔧 [API] Regenerating risk for requirement index {req_idx}")
                        try:
                            # Get the updated requirement to provide context
                            updated_requirement = current_requirements[req_idx]
                            updated_risk = generate_single_risk_with_feedback(
                                state, req_idx, f"Requirement was updated to: {updated_requirement}"
                            )
                            if updated_risk and updated_risk != current_risks[req_idx]:
                                current_risks[req_idx] = updated_risk
                                logger.info(f"✅ [API] Updated risk at index {req_idx}: '{updated_risk}'")
                            else:
                                logger.warning(f"⚠️ [API] No change for risk at index {req_idx}")
                        except Exception as e:
                            logger.error(f"❌ [API] Error updating risk at index {req_idx}: {e}")
                
                # Update the state with only the changed risks
                state["risks_output"].Risks = current_risks
                logger.info(f"🔧 [API] Final risks after selective update: {state['risks_output'].Risks}")
            else:
                logger.info("🔧 [API] No requirements changed, skipping risk regeneration")
            
        elif request.regenerate_type == "risks":
            if not state.get("risks_output"):
                raise HTTPException(status_code=400, detail="No risks available")
            
            # Store current risks
            current_risks = state["risks_output"].Risks.copy()
            
            logger.info(f"🔧 [API] Current risks before regeneration: {current_risks}")
            
            # Generate new risks with feedback - but only for the specific indexes
            updated_count = 0
            for idx in request.indexes:
                if idx < len(current_risks):
                    logger.info(f"🔧 [API] Calling generate_single_risk_with_feedback for index {idx}")
                    try:
                        updated_risk = generate_single_risk_with_feedback(
                            state, idx, request.feedback
                        )
                        logger.info(f"🔧 [API] Returned from generate_single_risk_with_feedback: '{updated_risk}'")
                        
                        if updated_risk and updated_risk != current_risks[idx]:
                            current_risks[idx] = updated_risk
                            updated_count += 1
                            logger.info(f"✅ [API] Updated risk at index {idx}: '{updated_risk}'")
                        else:
                            logger.warning(f"⚠️ [API] No change for risk at index {idx}")
                    except Exception as e:
                        logger.error(f"❌ [API] Error updating risk at index {idx}: {e}")
            
            # Update the state with only the changed risks
            state["risks_output"].Risks = current_risks
            
            logger.info(f"🔧 [API] Final risks after selective update: {state['risks_output'].Risks}")
            logger.info(f"🔧 [API] Successfully updated {updated_count} risks")
        
        # Update stored state
        workflow_states[thread_id] = state
        
        # Log the final response
        logger.info(f"🔧 [API] Returning response with {len(state['requirements_output'].requirements)} requirements and {len(state['risks_output'].Risks)} risks")
        
        return WorkflowResponse(
            thread_id=thread_id,
            status="regenerated",
            selected_keyword=state["selected_keyword"],
            requirements=state["requirements_output"].requirements if state.get("requirements_output") else None,
            risks=state["risks_output"].Risks if state.get("risks_output") else None,
            message=f"Regenerated {len(request.indexes)} {request.regenerate_type} with feedback"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating with feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/regenerate-requirements", response_model=WorkflowResponse)
async def regenerate_requirements(request: SelectiveRegenerateRequest):
    """Regenerate specific requirements by indexes."""
    try:
        thread_id = request.thread_id
        
        if thread_id not in workflow_states:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        state = workflow_states[thread_id]
        
        if not state.get("selected_keyword"):
            raise HTTPException(status_code=400, detail="No keyword selected")
        
        if not state.get("requirements_output"):
            raise HTTPException(status_code=400, detail="No requirements available")
        
        logger.info(f"Regenerating requirements at indexes: {request.requirement_indexes}")
        
        from backend.nodes.nodes import generate_requirements
        
        # Store current requirements
        current_requirements = state["requirements_output"].requirements.copy()
        
        # Generate new requirements
        state = generate_requirements(state)
        new_requirements = state["requirements_output"].requirements
        
        # Replace only the selected indexes with new requirements
        for idx in request.requirement_indexes:
            if idx < len(current_requirements) and idx < len(new_requirements):
                current_requirements[idx] = new_requirements[idx]
        
        # Update the state with mixed requirements
        state["requirements_output"].requirements = current_requirements
        
        # Update stored state
        workflow_states[thread_id] = state
        
        return WorkflowResponse(
            thread_id=thread_id,
            status="regenerated",
            selected_keyword=state["selected_keyword"],
            requirements=state["requirements_output"].requirements,
            risks=state["risks_output"].Risks if state.get("risks_output") else None,
            message=f"Regenerated {len(request.requirement_indexes)} requirements"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating requirements: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/regenerate-risks", response_model=WorkflowResponse)
async def regenerate_risks(request: SelectiveRegenerateRequest):
    """Regenerate specific risks by indexes."""
    try:
        thread_id = request.thread_id
        
        if thread_id not in workflow_states:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        state = workflow_states[thread_id]
        
        if not state.get("selected_keyword"):
            raise HTTPException(status_code=400, detail="No keyword selected")
        
        if not state.get("risks_output"):
            raise HTTPException(status_code=400, detail="No risks available")
        
        logger.info(f"Regenerating risks at indexes: {request.risk_indexes}")
        
        from backend.nodes.nodes import generate_risks
        
        # Store current risks
        current_risks = state["risks_output"].Risks.copy()
        
        # Generate new risks
        state = generate_risks(state)
        new_risks = state["risks_output"].Risks
        
        # Replace only the selected indexes with new risks
        for idx in request.risk_indexes:
            if idx < len(current_risks) and idx < len(new_risks):
                current_risks[idx] = new_risks[idx]
        
        # Update the state with mixed risks
        state["risks_output"].Risks = current_risks
        
        # Update stored state
        workflow_states[thread_id] = state
        
        return WorkflowResponse(
            thread_id=thread_id,
            status="regenerated",
            selected_keyword=state["selected_keyword"],
            requirements=state["requirements_output"].requirements if state.get("requirements_output") else None,
            risks=state["risks_output"].Risks,
            message=f"Regenerated {len(request.risk_indexes)} risks"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating risks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))