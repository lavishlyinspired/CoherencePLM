# backend/traceability/traceability_service.py
from typing import Dict, List, Optional, Any
from neo4j import GraphDatabase
import logging

from config import settings
logger = logging.getLogger(__name__)

class TraceabilityService:
    def __init__(self, driver):
        self.driver = driver

    def get_traceability_graph(self, project_name: str, requirement_id: Optional[str] = None) -> Dict[str, Any]:
        """Get traceability graph data for a project or specific requirement"""
        try:
            if requirement_id:
                return self._get_requirement_traceability(project_name, requirement_id)
            else:
                return self._get_project_traceability(project_name)
        except Exception as e:
            logger.error(f"Error in get_traceability_graph: {e}")
            raise

    def _get_project_traceability(self, project_name: str) -> Dict[str, Any]:
        """Get full project traceability graph"""
        query = """
        MATCH (p:Project {name: $project_name})
        OPTIONAL MATCH (p)-[:HAS_REQUIREMENT]->(r:Requirement)
        OPTIONAL MATCH (r)-[:HAS_RISK]->(rk:Risk)
        
        WITH p, r, rk
        
        // Create node objects
        WITH collect(DISTINCT {
            id: p.name,
            type: 'Project',
            label: p.name,
            properties: properties(p)
        }) as project_nodes,
        collect(DISTINCT CASE WHEN r IS NOT NULL THEN {
            id: 'REQ_' + toString(r.index),
            type: 'Requirement', 
            label: r.description,
            properties: properties(r)
        } END) as req_nodes,
        collect(DISTINCT CASE WHEN rk IS NOT NULL THEN {
            id: 'RISK_' + toString(rk.index),
            type: 'Risk',
            label: rk.description,
            properties: properties(rk)
        } END) as risk_nodes
        
        // Combine and filter nulls
        WITH (project_nodes + req_nodes + risk_nodes) as all_nodes
        UNWIND all_nodes as node
        WITH node WHERE node IS NOT NULL
        RETURN collect(node) as nodes
        """
        
        with self.driver.session(database=settings.neo4j_database) as session:
            result = session.run(query, project_name=project_name)
            record = result.single()
            nodes_data = record["nodes"] if record else []
            
            # Get relationships
            links = self._get_relationships(project_name)
            
            logger.info(f"Found {len(nodes_data)} nodes and {len(links)} links for project {project_name}")
            
            return {
                "nodes": nodes_data,
                "links": links
            }

    def _get_relationships(self, project_name: str) -> List[Dict[str, Any]]:
        """Get all relationships for a project"""
        query = """
        MATCH (p:Project {name: $project_name})-[:HAS_REQUIREMENT]->(r:Requirement)
        OPTIONAL MATCH (r)-[:HAS_RISK]->(rk:Risk)
        
        WITH r, rk
        WHERE rk IS NOT NULL
        
        RETURN collect({
            source: 'REQ_' + toString(r.index),
            target: 'RISK_' + toString(rk.index),
            type: 'HAS_RISK'
        }) as relationships
        """
        
        with self.driver.session(database=settings.neo4j_database) as session:
            result = session.run(query, project_name=project_name)
            record = result.single()
            return record["relationships"] if record else []

    def _get_requirement_traceability(self, project_name: str, requirement_id: str) -> Dict[str, Any]:
        """Get traceability for a specific requirement"""
        # Extract the index from requirement_id (e.g., "REQ_1" -> 1)
        try:
            req_index = int(requirement_id.split('_')[-1])
        except:
            req_index = 1
        
        query = """
        MATCH (p:Project {name: $project_name})-[:HAS_REQUIREMENT]->(r:Requirement {index: $req_index})
        OPTIONAL MATCH (r)-[:HAS_RISK]->(rk:Risk)
        
        WITH r, rk
        
        WITH collect(DISTINCT {
            id: 'REQ_' + toString(r.index),
            type: 'Requirement',
            label: r.description,
            properties: properties(r)
        }) as req_nodes,
        collect(DISTINCT CASE WHEN rk IS NOT NULL THEN {
            id: 'RISK_' + toString(rk.index),
            type: 'Risk',
            label: rk.description,
            properties: properties(rk)
        } END) as risk_nodes
        
        WITH (req_nodes + risk_nodes) as all_nodes
        UNWIND all_nodes as node
        WITH node WHERE node IS NOT NULL
        RETURN collect(node) as nodes
        """
        
        with self.driver.session(database=settings.neo4j_database) as session:
            result = session.run(query, project_name=project_name, req_index=req_index)
            record = result.single()
            nodes_data = record["nodes"] if record else []
            
            # Get relationships for this requirement
            links = self._get_requirement_relationships(project_name, req_index)
            
            return {
                "nodes": nodes_data,
                "links": links
            }

    def _get_requirement_relationships(self, project_name: str, req_index: int) -> List[Dict[str, Any]]:
        """Get relationships for a specific requirement"""
        query = """
        MATCH (r:Requirement {project: $project_name, index: $req_index})-[:HAS_RISK]->(rk:Risk)
        RETURN collect({
            source: 'REQ_' + toString(r.index),
            target: 'RISK_' + toString(rk.index),
            type: 'HAS_RISK'
        }) as relationships
        """
        
        with self.driver.session(database=settings.neo4j_database) as session:
            result = session.run(query, project_name=project_name, req_index=req_index)
            record = result.single()
            return record["relationships"] if record else []

    def get_traceability_table(self) -> List[Dict[str, Any]]:
        """Get data for traceability table view"""
        query = """
        MATCH (r:Requirement)
        OPTIONAL MATCH (r)-[:HAS_RISK]->(risk:Risk)
        
        WITH r, 
             collect(DISTINCT risk) as risks,
             r.description as req_desc,
             coalesce(r.id, 'REQ_' + toString(r.index)) as req_id,
             coalesce(r.priority, 'Medium') as req_priority
        
        RETURN {
            requirement: {
                id: req_id,
                title: coalesce(r.name, 'Requirement ' + toString(r.index)),
                description: req_desc,
                priority: req_priority
            },
            business_need: null,
            sources: [],
            risks: [risk in risks WHERE risk IS NOT NULL | {
                id: coalesce(risk.id, 'RISK_' + toString(risk.index)),
                title: coalesce(risk.name, 'Risk ' + toString(risk.index)),
                description: risk.description,
                severity: coalesce(risk.severity, 'Medium'),
                mitigation: coalesce(risk.mitigation, 'To be determined')
            }],
            test_cases: []
        } as traceability_data
        ORDER BY req_desc
        """
        
        with self.driver.session(database=settings.neo4j_database) as session:
            result = session.run(query)
            data = [record["traceability_data"] for record in result]
            
            logger.info(f"Found {len(data)} requirements for traceability table")
            
            return data

    def get_traceability_projects(self) -> List[str]:
        """Get list of projects available for traceability"""
        query = "MATCH (p:Project) RETURN p.name as name ORDER BY p.name"
        
        with self.driver.session(database=settings.neo4j_database) as session:
            result = session.run(query)
            projects = [record["name"] for record in result]
            logger.info(f"Found {len(projects)} projects: {projects}")
            return projects