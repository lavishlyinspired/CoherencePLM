"""
Unit tests for FastAPI endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from api import app
from models import KeywordOutput, RequirementsOutput, RisksOutput

client = TestClient(app)

class TestAPIEndpoints:
    """Test cases for API endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    @patch('api.workflow_graph')
    def test_create_project(self, mock_graph):
        """Test project creation endpoint."""
        mock_state = {
            "keyword_output": KeywordOutput(keywords=["kw1", "kw2", "kw3", "kw4", "kw5"]),
            "messages": []
        }
        mock_graph.stream.return_value = [mock_state]
        
        response = client.post(
            "/project/create",
            json={
                "requirement_description": "Test requirement",
                "project_name": "test_project"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["thread_id"] == "test_project"
        assert data["status"] == "keywords_generated"
        assert len(data["keywords"]) == 5
    
    @patch('api.workflow_graph')
    def test_select_keyword(self, mock_graph):
        """Test keyword selection endpoint."""
        # Setup mock workflow state
        from api import workflow_states
        workflow_states["test_thread"] = {
            "keyword_output": KeywordOutput(keywords=["kw1", "kw2", "kw3", "kw4", "kw5"]),
            "requirements_output": None,
            "risks_output": None,
            "messages": []
        }
        
        mock_state_with_req = {
            "requirements_output": RequirementsOutput(requirements=["R1", "R2", "R3", "R4", "R5"]),
            "risks_output": RisksOutput(Risks=["Rsk1", "Rsk2", "Rsk3", "Rsk4", "Rsk5"]),
            "selected_keyword": "kw1"
        }
        mock_graph.stream.return_value = [mock_state_with_req]
        
        response = client.post(
            "/project/select-keyword",
            json={
                "thread_id": "test_thread",
                "keyword_index": 0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "generated"
        assert len(data["requirements"]) == 5
        assert len(data["risks"]) == 5
    
    def test_select_keyword_invalid_thread(self):
        """Test keyword selection with invalid thread ID."""
        response = client.post(
            "/project/select-keyword",
            json={
                "thread_id": "nonexistent",
                "keyword_index": 0
            }
        )
        
        assert response.status_code == 404
    
    @patch('api.workflow_graph')
    def test_regenerate_requirements(self, mock_graph):
        """Test requirements regeneration endpoint."""
        from api import workflow_states
        workflow_states["test_thread"] = {
            "selected_keyword": "test keyword",
            "requirements_output": RequirementsOutput(requirements=["R1"] * 5),
            "risks_output": RisksOutput(Risks=["Rsk1"] * 5),
            "messages": []
        }
        
        mock_state = {
            "requirements_output": RequirementsOutput(requirements=["New R1", "New R2", "New R3", "New R4", "New R5"]),
            "risks_output": RisksOutput(Risks=["Rsk1"] * 5)
        }
        mock_graph.stream.return_value = [mock_state]
        
        response = client.post(
            "/project/regenerate",
            json={
                "thread_id": "test_thread",
                "regenerate_type": "requirements"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "regenerated"
    
    @patch('api.workflow_graph')
    def test_save_project(self, mock_graph):
        """Test project save endpoint."""
        from api import workflow_states
        workflow_states["test_thread"] = {
            "selected_keyword": "test keyword",
            "requirements_output": RequirementsOutput(requirements=["R1"] * 5),
            "risks_output": RisksOutput(Risks=["Rsk1"] * 5),
            "messages": []
        }
        
        mock_graph.stream.return_value = [workflow_states["test_thread"]]
        
        response = client.post("/project/save?thread_id=test_thread")
        
        assert response.status_code == 200
        assert response.json()["status"] == "saved"
    
    def test_get_project(self):
        """Test get project endpoint."""
        from api import workflow_states
        workflow_states["test_thread"] = {
            "keyword_output": KeywordOutput(keywords=["kw1", "kw2", "kw3", "kw4", "kw5"]),
            "selected_keyword": "kw1",
            "requirements_output": RequirementsOutput(requirements=["R1"] * 5),
            "risks_output": RisksOutput(Risks=["Rsk1"] * 5),
            "messages": []
        }
        
        response = client.get("/project/test_thread")
        
        assert response.status_code == 200
        data = response.json()
        assert data["thread_id"] == "test_thread"
        assert data["status"] == "active"
    
    def test_list_projects(self):
        """Test list projects endpoint."""
        from api import workflow_states
        workflow_states.clear()
        workflow_states["proj1"] = {}
        workflow_states["proj2"] = {}
        
        response = client.get("/projects")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert "proj1" in data["projects"]

