"""Traceability-related API routes."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.logger.logger import logger
from backend.tools.tools import graph_db
from traceability.traceability_service import TraceabilityService
from traceability.schema import TraceabilitySchema
from neo4j import GraphDatabase
from backend.config.config import settings
router = APIRouter()
driver = GraphDatabase.driver(
            settings.neo4j_url,
            auth=(settings.neo4j_username, settings.neo4j_password)
        )   
# Initialize the service
traceability_service = TraceabilityService(driver)

@router.get("/traceability-graph")
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

@router.get("/traceability-table")
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

@router.get("/traceability-projects")
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

@router.post("/init-traceability-schema")
async def init_traceability_schema():
    """Initialize traceability schema (for development)"""
    try:
        TraceabilitySchema.create_schema(graph_db.driver)
        TraceabilitySchema.create_sample_data(graph_db.driver)
        return {"message": "Traceability schema initialized successfully"}
    except Exception as e:
        logger.error(f"Error initializing traceability schema: {e}")
        raise HTTPException(status_code=500, detail=f"Error initializing traceability schema: {str(e)}")