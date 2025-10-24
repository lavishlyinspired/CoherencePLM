"""
Pytest configuration and fixtures.
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture(autouse=True)
def reset_workflow_states():
    """Reset workflow states before each test."""
    from backend.api.api import workflow_states
    workflow_states.clear()
    yield
    workflow_states.clear()
