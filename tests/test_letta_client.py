"""
Unit tests for letta_client.py
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from letta_api import LettaClient
from letta_client import MessageCreate

class TestLettaClient:
    @pytest.fixture
    def client(self, mock_env_vars):
        """Create LettaClient instance for testing"""
        with patch('letta_api.config') as mock_config:
            mock_config.default_agent_id = "agent_123"
            mock_config.letta_server_url = "https://test-server.com:8283"
            mock_config.letta_api_token = "test_token_123"
            return LettaClient()
    
    def test_initialization(self, client, mock_env_vars):
        """Test client initialization"""
        assert client.current_agent_id == "agent_123"
        assert client.client is not None
    
    def test_test_connection_success(self, client):
        """Test successful connection"""
        client.client.health.check.return_value = Mock(version="0.1.324", status="ok")
        assert client.test_connection() is True
        client.client.health.check.assert_called_once()
    
    def test_test_connection_failure(self, client):
        """Test connection failure"""
        client.client.health.check.side_effect = Exception("Connection failed")
        assert client.test_connection() is False
        client.client.health.check.assert_called_once()
    
    def test_list_agents_success(self, client, sample_agents):
        """Test successful agent listing"""
        # Setup mock agents
        mock_agents = []
        for agent_data in sample_agents:
            mock_agent = Mock()
            mock_agent.id = agent_data["id"]
            mock_agent.name = agent_data["name"]
            mock_agent.description = agent_data["description"]
            mock_agents.append(mock_agent)
        
        client.client.agents.list.return_value = mock_agents
        agents = client.list_agents()
        
        assert len(agents) == 2
        assert agents[0]["id"] == "agent_123"
        assert agents[0]["name"] == "Test Agent 1"
        assert agents[1]["id"] == "agent_456"
        assert agents[1]["name"] == "Test Agent 2"
    
    def test_list_agents_failure(self, client):
        """Test agent listing failure"""
        client.client.agents.list.side_effect = Exception("API Error")
        agents = client.list_agents()
        assert agents == []
    
    def test_set_agent(self, client):
        """Test setting agent"""
        result = client.set_agent("agent_456")
        assert result is True
        assert client.current_agent_id == "agent_456"
    
    def test_send_message_success(self, client):
        """Test successful message sending"""
        client.current_agent_id = "agent_123"
        mock_response = Mock()
        mock_response.content = "Test response"
        client.client.agents.messages.create.return_value = mock_response
        
        response = client.send_message("Hello")
        
        assert response == "Test response"
        client.client.agents.messages.create.assert_called_once_with(
            agent_id="agent_123",
            messages=[MessageCreate(role="user", content="Hello")]
        )
    
    def test_send_message_no_agent(self, client):
        """Test sending message with no agent selected"""
        client.current_agent_id = None
        response = client.send_message("Hello")
        assert response is None
        client.client.agents.messages.create.assert_not_called()
    
    def test_send_message_failure(self, client):
        """Test message sending failure"""
        client.current_agent_id = "agent_123"
        client.client.agents.messages.create.side_effect = Exception("API Error")
        
        response = client.send_message("Hello")
        assert response is None
    
    @pytest.mark.asyncio
    async def test_send_message_stream_success(self, client):
        """Test successful message streaming"""
        client.current_agent_id = "agent_123"
        
        # Mock streaming response
        mock_chunk1 = Mock()
        mock_chunk1.content = "Hello "
        mock_chunk2 = Mock()
        mock_chunk2.content = "world!"
        
        client.client.agents.messages.create_stream.return_value = [mock_chunk1, mock_chunk2]
        
        chunks = []
        async for chunk in client.send_message_stream("Hello"):
            chunks.append(chunk)
        
        assert chunks == ["Hello ", "world!"]
        client.client.agents.messages.create_stream.assert_called_once_with(
            agent_id="agent_123",
            messages=[MessageCreate(role="user", content="Hello")]
        )
    
    @pytest.mark.asyncio
    async def test_send_message_stream_no_agent(self, client):
        """Test streaming with no agent selected"""
        client.current_agent_id = None
        
        chunks = []
        async for chunk in client.send_message_stream("Hello"):
            chunks.append(chunk)
        
        assert chunks == []
        client.client.agents.messages.create_stream.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_send_message_stream_failure(self, client):
        """Test streaming failure"""
        client.current_agent_id = "agent_123"
        client.client.agents.messages.create_stream.side_effect = Exception("Stream Error")
        
        chunks = []
        async for chunk in client.send_message_stream("Hello"):
            chunks.append(chunk)
        
        assert len(chunks) == 1
        assert "Error: Stream Error" in chunks[0]
