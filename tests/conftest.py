"""
Shared test fixtures and configuration
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from letta_client import Letta as LettaClient

@pytest.fixture
def temp_env_file():
    """Create a temporary .env file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as tmp:
        tmp.write("""# Test environment
LETTA_SERVER_URL=https://test-server.com:8283
LETTA_API_TOKEN=test_token_123
DISPLAY_NAME=TestUser
DEFAULT_AGENT_ID=agent_123
""")
        tmp.flush()
        yield tmp.name
    # Cleanup
    try:
        os.unlink(tmp.name)
    except (PermissionError, OSError):
        pass

@pytest.fixture
def mock_letta_client():
    """Mock Letta client for testing"""
    client = Mock()
    
    # Mock health check
    client.health = Mock()
    client.health.check.return_value = Mock(version="0.1.324", status="ok")
    
    # Mock agents
    client.agents = Mock()
    mock_agent1 = Mock()
    mock_agent1.id = "agent_123"
    mock_agent1.name = "Test Agent 1"
    mock_agent1.description = "First test agent"
    
    mock_agent2 = Mock()
    mock_agent2.id = "agent_456"
    mock_agent2.name = "Test Agent 2"
    mock_agent2.description = "Second test agent"
    
    client.agents.list.return_value = [mock_agent1, mock_agent2]
    
    # Mock messages
    client.agents.messages = Mock()
    mock_response = Mock()
    mock_response.content = "Test response from agent"
    client.agents.messages.create.return_value = mock_response
    
    # Mock streaming
    mock_chunk = Mock()
    mock_chunk.content = "Streaming response chunk"
    client.agents.messages.create_stream.return_value = [mock_chunk]
    
    return client

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables"""
    monkeypatch.setenv("LETTA_SERVER_URL", "https://test-server.com:8283")
    monkeypatch.setenv("LETTA_API_TOKEN", "test_token_123")
    monkeypatch.setenv("DISPLAY_NAME", "TestUser")
    monkeypatch.setenv("DEFAULT_AGENT_ID", "agent_123")

@pytest.fixture
def sample_agents():
    """Sample agent data for testing"""
    return [
        {"id": "agent_123", "name": "Test Agent 1", "description": "First test agent"},
        {"id": "agent_456", "name": "Test Agent 2", "description": "Second test agent"},
    ]
