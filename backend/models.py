"""Pydantic models for data validation and serialization."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class KeywordOutput(BaseModel):
    """Model for keyword generation output."""
    keywords: List[str] = Field(..., description="5 keywords, each 3 words long")

class RequirementsOutput(BaseModel):
    """Model for requirements generation output."""
    requirements: List[str] = Field(..., description="generate formal requirements")

class RisksOutput(BaseModel):
    """Model for risk generation output."""
    Risks: List[str] = Field(..., description="generate risk for the requirement")

class ProjectRequest(BaseModel):
    """Model for project creation request."""
    requirement_description: str = Field(..., description="Description of the requirement")
    project_name: Optional[str] = Field(None, description="Name of the project")

class KeywordSelectionRequest(BaseModel):
    """Model for keyword selection."""
    thread_id: str
    keyword_index: int = Field(..., ge=0, lt=5)

class RegenerateRequest(BaseModel):
    """Model for regeneration request."""
    thread_id: str
    regenerate_type: str = Field(..., description="'requirements', 'risks', or 'both'")

class SelectiveRegenerateRequest(BaseModel):
    """Model for selective regeneration request."""
    thread_id: str
    requirement_indexes: Optional[List[int]] = Field(None, description="Indexes of requirements to regenerate")
    risk_indexes: Optional[List[int]] = Field(None, description="Indexes of risks to regenerate")

class SelectiveSaveRequest(BaseModel):
    """Model for selective save request."""
    thread_id: str
    requirements: List[str] = Field(..., description="Selected requirements to save")
    risks: List[str] = Field(..., description="Corresponding risks to save")
    keyword: str = Field(..., description="Selected keyword")

class RiskUpdateRequest(BaseModel):
    """Model for risk update request."""
    thread_id: str
    risk_data: List[Dict[str, Any]] = Field(..., description="Risk data to update")

class WorkflowResponse(BaseModel):
    """Model for workflow response."""
    thread_id: str
    status: str
    keywords: Optional[List[str]] = None
    selected_keyword: Optional[str] = None
    requirements: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    message: Optional[str] = None


"""Pydantic models for data validation and serialization."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any



class FeedbackRequest(BaseModel):
    """Model for feedback-based regeneration."""
    thread_id: str
    indexes: List[int] = Field(..., description="Indexes of items to regenerate")
    feedback: str = Field(..., description="Feedback for regeneration")
    regenerate_type: str = Field(..., description="'requirements' or 'risks'")

class DetailedItem(BaseModel):
    """Model for detailed item view."""
    index: int
    type: str  # 'requirement' or 'risk'
    content: str
    related_items: List[str] = Field(default_factory=list)
    feedback_history: List[str] = Field(default_factory=list)

class ItemUpdateRequest(BaseModel):
    """Model for manual item updates."""
    thread_id: str
    index: int
    type: str  # 'requirement' or 'risk'
    new_content: str
    update_related: bool = Field(default=True, description="Whether to update related items")

# Add to models.py
class TestsOutput(BaseModel):
    """Model for test case generation output."""
    test_cases: List[Dict[str, Any]] = Field(..., description="Generated test cases")

class TestCaseRequest(BaseModel):
    """Model for test case generation request."""
    thread_id: str
    requirement_index: int = Field(..., ge=0, lt=5)

class TestCaseUpdateRequest(BaseModel):
    """Model for test case update request."""
    thread_id: str
    requirement_index: int
    test_cases: List[Dict[str, Any]]