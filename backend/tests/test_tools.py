"""
Unit tests for tools module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.tools.tools import save_to_neo4j, get_project_data

@pytest.fixture
def mock_neo4j_graph():
    """Mock Neo4j graph database."""
    with patch('tools.graph_db') as mock_graph:
        mock_graph.query = Mock(return_value=[])
        yield mock_graph

class TestSaveToNeo4j:
    """Test cases for save_to_neo4j tool."""

    def test_save_successful(self, mock_neo4j_graph):
        """Test successful save operation."""
        requirements = [
            "Req 1: System must support...",
            "Req 2: Application shall...",
            "Req 3: Platform should..."
        ]
        risks = [
            "Risk 1: Performance degradation",
            "Risk 2: Security vulnerability",
            "Risk 3: Scalability issues"
        ]

        result = save_to_neo4j.invoke({
            "requirements": requirements,
            "risks": risks,
            "project_name": "test_project",
            "keyword": "test keyword phrase"
        })

        assert "Successfully saved" in result
        assert "3 requirements" in result
        assert "3 risks" in result
        assert mock_neo4j_graph.query.called

    def test_save_with_error(self, mock_neo4j_graph):
        """Test save operation with database error."""
        mock_neo4j_graph.query.side_effect = Exception("Database connection failed")

        result = save_to_neo4j.invoke({
            "requirements": ["Test req"],
            "risks": ["Test risk"],
            "project_name": "test_project",
            "keyword": "test keyword"
        })

        assert "Error saving to Neo4j" in result
        assert "Database connection failed" in result

    def test_save_empty_lists(self, mock_neo4j_graph):
        """Test save with empty requirements and risks."""
        result = save_to_neo4j.invoke({
            "requirements": [],
            "risks": [],
            "project_name": "test_project",
            "keyword": "test keyword"
        })

        assert "Successfully saved" in result
        assert "0 requirements" in result

class TestGetProjectData:
    """Test cases for get_project_data function."""

    def test_get_existing_project(self, mock_neo4j_graph):
        """Test retrieving existing project data."""
        mock_result = [{
            'p': {'name': 'test_project', 'keyword': 'test keyword'},
            'requirements': [{'description': 'Req 1'}],
            'risks': [{'description': 'Risk 1'}]
        }]
        mock_neo4j_graph.query.return_value = mock_result

        result = get_project_data("test_project")

        assert result is not None
        assert result['p']['name'] == 'test_project'
        mock_neo4j_graph.query.assert_called_once()

    def test_get_nonexistent_project(self, mock_neo4j_graph):
        """Test retrieving non-existent project."""
        mock_neo4j_graph.query.return_value = []

        result = get_project_data("nonexistent_project")

        assert result is None

    def test_get_project_with_error(self, mock_neo4j_graph):
        """Test get project with database error."""
        mock_neo4j_graph.query.side_effect = Exception("Query failed")

        result = get_project_data("test_project")

        assert result is None
