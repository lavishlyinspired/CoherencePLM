"""
Unit tests for nodes module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from nodes import (
    generate_keywords,
    generate_requirements,
    generate_risks,
    call_save_tool,
    KeywordState
)
from models import KeywordOutput, RequirementsOutput, RisksOutput

@pytest.fixture
def base_state():
    """Create base state for testing."""
    return {
        "requirement_description": "Test requirement description",
        "messages": [],
        "keyword_output": None,
        "selected_keyword": None,
        "requirements_output": None,
        "risks_output": None,
        "project_name": "test_project"
    }

class TestGenerateKeywords:
    """Test cases for generate_keywords node."""
    
    @patch('nodes.llm')
    def test_generate_keywords_successful(self, mock_llm, base_state):
        """Test successful keyword generation."""
        mock_keywords = KeywordOutput(keywords=[
            "keyword one phrase",
            "keyword two phrase",
            "keyword three phrase",
            "keyword four phrase",
            "keyword five phrase"
        ])
        
        mock_structured_llm = Mock()
        mock_structured_llm.invoke.return_value = mock_keywords
        mock_llm.with_structured_output.return_value = mock_structured_llm
        
        result = generate_keywords(base_state)
        
        assert result["keyword_output"] is not None
        assert len(result["keyword_output"].keywords) == 5
        assert len(result["messages"]) == 1
    
    @patch('nodes.llm')
    def test_generate_keywords_error(self, mock_llm, base_state):
        """Test keyword generation with error."""
        mock_llm.with_structured_output.side_effect = Exception("LLM error")
        
        with pytest.raises(Exception):
            generate_keywords(base_state)

class TestGenerateRequirements:
    """Test cases for generate_requirements node."""
    
    @patch('nodes.llm')
    def test_generate_requirements_successful(self, mock_llm, base_state):
        """Test successful requirements generation."""
        base_state["selected_keyword"] = "test keyword phrase"
        
        mock_requirements = RequirementsOutput(requirements=[
            "Requirement 1",
            "Requirement 2",
            "Requirement 3",
            "Requirement 4",
            "Requirement 5"
        ])
        
        mock_structured_llm = Mock()
        mock_structured_llm.invoke.return_value = mock_requirements
        mock_llm.with_structured_output.return_value = mock_structured_llm
        
        result = generate_requirements(base_state)
        
        assert result["requirements_output"] is not None
        assert len(result["requirements_output"].requirements) == 5
        assert len(result["messages"]) == 1
    
    @patch('nodes.llm')
    def test_generate_requirements_clears_regenerate_flag(self, mock_llm, base_state):
        """Test that regenerate flag is cleared after generation."""
        base_state["selected_keyword"] = "test keyword"
        base_state["regenerate_flag"] = "requirements"
        
        mock_requirements = RequirementsOutput(requirements=["Req 1"] * 5)
        mock_structured_llm = Mock()
        mock_structured_llm.invoke.return_value = mock_requirements
        mock_llm.with_structured_output.return_value = mock_structured_llm
        
        result = generate_requirements(base_state)
        
        assert result.get("regenerate_flag") is None

class TestGenerateRisks:
    """Test cases for generate_risks node."""
    
    @patch('nodes.llm')
    def test_generate_risks_successful(self, mock_llm, base_state):
        """Test successful risk generation."""
        base_state["requirements_output"] = RequirementsOutput(
            requirements=["Req 1", "Req 2", "Req 3", "Req 4", "Req 5"]
        )
        
        mock_risks = RisksOutput(Risks=[
            "Risk 1",
            "Risk 2",
            "Risk 3",
            "Risk 4",
            "Risk 5"
        ])
        
        mock_structured_llm = Mock()
        mock_structured_llm.invoke.return_value = mock_risks
        mock_llm.with_structured_output.return_value = mock_structured_llm
        
        result = generate_risks(base_state)
        
        assert result["risks_output"] is not None
        assert len(result["risks_output"].Risks) == 5

class TestCallSaveTool:
    """Test cases for call_save_tool node."""
    
    @patch('nodes.save_to_neo4j')
    def test_save_tool_successful(self, mock_save_tool, base_state):
        """Test successful save operation."""
        base_state["requirements_output"] = RequirementsOutput(
            requirements=["Req 1", "Req 2", "Req 3", "Req 4", "Req 5"]
        )
        base_state["risks_output"] = RisksOutput(
            Risks=["Risk 1", "Risk 2", "Risk 3", "Risk 4", "Risk 5"]
        )
        base_state["selected_keyword"] = "test keyword"
        
        mock_save_tool.invoke.return_value = "Successfully saved"
        
        result = call_save_tool(base_state)
        
        assert len(result["messages"]) == 1
        mock_save_tool.invoke.assert_called_once()