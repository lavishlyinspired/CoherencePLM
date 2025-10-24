"""project -specific operations routes."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from backend.logger.logger import logger
from backend.tools.tools import graph_db
from backend.model.models import ItemUpdateRequest, WorkflowResponse
from api.shared.state import workflow_states

router = APIRouter()
@router.get("/debug-projects")
async def debug_projects():
    """Debug endpoint to see what projects exist in Neo4j"""
    try:
        logger.info("=== Starting debug_projects endpoint ===")
        
        from backend.tools.tools import graph_db
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
    
    
