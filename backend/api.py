"""FastAPI application for requirements management."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional

import uuid
from datetime import datetime

from config import settings
from models import (
    ProjectRequest,
    KeywordSelectionRequest,
    RegenerateRequest,
    WorkflowResponse,
    FeedbackRequest,
    SelectiveRegenerateRequest,
    SelectiveSaveRequest,
    RiskUpdateRequest,
    ItemUpdateRequest,
    TestCaseRequest,
    TestCaseUpdateRequest
)
from graph import workflow_graph
from logger import logger
from tools import save_to_neo4j

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Requirements Management API with LangGraph and Neo4j"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

workflow_states: Dict[str, dict] = {}

def safe_log_message(message: str) -> str:
    """Safely encode message for logging by replacing problematic Unicode characters."""
    replacements = {
        '\u202f': ' ',  # Narrow no-break space -> regular space
        '\u00a0': ' ',  # No-break space -> regular space
        '\u2018': "'",  # Left single quotation mark
        '\u2019': "'",  # Right single quotation mark
        '\u201c': '"',  # Left double quotation mark
        '\u201d': '"',  # Right double quotation mark
        '\u2013': '-',  # En dash
        '\u2014': '-',  # Em dash,
    }
    for unicode_char, replacement in replacements.items():
        message = message.replace(unicode_char, replacement)
    return message

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.api_title} v{settings.api_version}")

@app.get("/")
async def root():
    return {
        "message": "Requirements Management API",
        "version": settings.api_version,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/project/create", response_model=WorkflowResponse)
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

@app.post("/project/select-keyword", response_model=WorkflowResponse)
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
        from nodes import generate_requirements, generate_risks
        
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
            from models import RisksOutput
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

@app.post("/project/regenerate", response_model=WorkflowResponse)
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
        
        from nodes import generate_requirements, generate_risks
        
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
    
@app.post("/project/regenerate-with-feedback", response_model=WorkflowResponse)
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
        from nodes import (
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
@app.post("/project/regenerate-requirements", response_model=WorkflowResponse)
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
        
        from nodes import generate_requirements
        
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

@app.post("/project/regenerate-risks", response_model=WorkflowResponse)
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
        
        from nodes import generate_risks
        
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

@app.post("/project/save-selected")
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

@app.post("/project/update-risks")
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
        from tools import graph_db
        
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

@app.post("/project/update-single-risk")
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
        from tools import graph_db
        
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

@app.post("/project/save")
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
        from nodes import call_save_tool
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

@app.get("/project/{thread_id}", response_model=WorkflowResponse)
async def get_project(thread_id: str):
    """Get project status."""
    try:
        if thread_id not in workflow_states:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        state = workflow_states[thread_id]
        
        return WorkflowResponse(
            thread_id=thread_id,
            status="active",
            keywords=state["keyword_output"].keywords if state.get("keyword_output") else None,
            selected_keyword=state.get("selected_keyword"),
            requirements=state["requirements_output"].requirements if state.get("requirements_output") else None,
            risks=state["risks_output"].Risks if state.get("risks_output") else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects")
async def list_projects():
    """List all projects."""
    return {
        "projects": list(workflow_states.keys()),
        "count": len(workflow_states)
    }
@app.get("/projects/debug-projects")
async def debug_projects():
    """Debug endpoint to see what projects exist in Neo4j"""
    try:
        logger.info("=== Starting debug_projects endpoint ===")
        
        from tools import graph_db
        logger.info("✓ Successfully imported graph_db")
        
        # Simple test query first
        test_result = graph_db.query("RETURN 'test' as result")
        logger.info(f"✓ Neo4j connection test: {test_result}")
        
        # Get all projects from Neo4j
        logger.info("✓ Executing Neo4j query for projects...")
        result = graph_db.query("""
            MATCH (p:Project)
            RETURN p.name AS name
            ORDER BY p.name
        """)
        
        logger.info(f"✓ Neo4j query returned: {result}")
        
        projects = []
        if result:
            projects = [record["name"] for record in result]
            logger.info(f"✓ Found projects: {projects}")
        else:
            logger.info("✓ No projects found in Neo4j")
        
        response = {
            "projects": projects,
            "count": len(projects),
            "message": f"Found {len(projects)} projects in Neo4j database"
        }
        
        logger.info(f"=== Returning response: {response} ===")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error in debug_projects: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/project/update-item", response_model=WorkflowResponse)
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
                from nodes import generate_risks
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
    
from fastapi import Request, Query
@app.get("/project/risks-from-neo4j")
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
    
@app.post("/project/search-risks")
async def search_risks(query: str):
    """Search risks in Neo4j database."""
    try:
        from tools import graph_db
        
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
from fastapi import FastAPI, HTTPException, Query
from tools import graph_db
import logging
@app.post("/project/load-from-neo4j")
async def load_project_from_neo4j(project_name: str = Query(...)):
    """
    Load a project from Neo4j into memory and return requirements + risks,
    associating each risk with its requirement.
    """
    try:
        from tools import graph_db
        from models import RequirementsOutput, RisksOutput
        
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
# Add to api.py
@app.post("/project/generate-test-cases", response_model=WorkflowResponse)
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
        
        from nodes import generate_test_cases
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

@app.post("/project/save-test-cases")
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
        
        from tools import save_test_cases_to_neo4j
        
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

@app.get("/project/test-cases/{thread_id}/{requirement_index}")
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
    # Add to your existing imports
from traceability.traceability_service import TraceabilityService
from traceability.schema import TraceabilitySchema
from neo4j import GraphDatabase


from config import settings
driver = GraphDatabase.driver(
            settings.neo4j_url,
            auth=(settings.neo4j_username, settings.neo4j_password)
        )   
# Initialize the service (add this after your existing imports)
traceability_service = TraceabilityService(driver)  # Assuming graph_db is your Neo4j client

# Add these routes to your existing API

@app.get("/api/traceability-graph")
async def get_traceability_graph(
    project_name: str = Query(..., description="Project name"),
    requirement_id: Optional[str] = Query(None, description="Specific requirement ID")
):
    """Get traceability graph for visualization"""
    try:
        logger.info(f"📊 Getting traceability graph for project: {project_name}")
        result = traceability_service.get_traceability_graph(project_name, requirement_id)
        logger.info(f"✅ Found {len(result.get('nodes', []))} nodes and {len(result.get('links', []))} links")
        return result
    except Exception as e:
        logger.error(f"❌ Error retrieving traceability graph: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving traceability graph: {str(e)}")

@app.get("/api/traceability-table")
async def get_traceability_table():
    """Get traceability table data"""
    try:
        logger.info("📋 Getting traceability table data")
        result = traceability_service.get_traceability_table()
        logger.info(f"✅ Found {len(result)} requirements")
        return result
    except Exception as e:
        logger.error(f"❌ Error retrieving traceability table: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving traceability table: {str(e)}")

@app.get("/api/traceability-projects")
async def get_traceability_projects():
    """Get list of projects available for traceability"""
    try:
        logger.info("📁 Getting traceability projects")
        projects = traceability_service.get_traceability_projects()
        logger.info(f"✅ Found {len(projects)} projects")
        return {"projects": projects}
    except Exception as e:
        logger.error(f"❌ Error retrieving traceability projects: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving traceability projects: {str(e)}")


@app.post("/api/init-traceability-schema")
async def init_traceability_schema():
    """Initialize traceability schema (for development)"""
    try:
        TraceabilitySchema.create_schema(graph_db.driver)
        TraceabilitySchema.create_sample_data(graph_db.driver)
        return {"message": "Traceability schema initialized successfully"}
    except Exception as e:
        logger.error(f"Error initializing traceability schema: {e}")
        raise HTTPException(status_code=500, detail=f"Error initializing traceability schema: {str(e)}")
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )