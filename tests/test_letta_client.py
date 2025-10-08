"""
Unit tests for letta_client.py
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from letta_api import LettaClient
from letta_client import MessageCreate

class TestLettaClient:

    def test_initialization(self, mock_env_vars):
        """Test client initialization"""
        with patch('letta_api.LettaSDK') as mock_letta_sdk, \
             patch('letta_api.config') as mock_config:
            mock_client = Mock()
            mock_letta_sdk.return_value = mock_client
            mock_config.default_agent_id = "agent_123"
            mock_config.letta_server_url = "https://test-server.com:8283"
            mock_config.letta_api_token = "test_token_123"
            client = LettaClient()
            assert client.current_agent_id == "agent_123"
            assert client.client is not None

    def test_test_connection_success(self, mock_env_vars):
        """Test successful connection"""
        with patch('letta_api.LettaSDK') as mock_letta_sdk:
            mock_client = Mock()
            mock_client.health.check.return_value = Mock(version="0.1.324", status="ok")
            mock_letta_sdk.return_value = mock_client
            client = LettaClient()
            assert client.test_connection() is True
            mock_client.health.check.assert_called_once()

    def test_test_connection_failure(self, mock_env_vars):
        """Test connection failure"""
        with patch('letta_api.LettaSDK') as mock_letta_sdk:
            mock_client = Mock()
            mock_client.health.check.side_effect = Exception("Connection failed")
            mock_letta_sdk.return_value = mock_client
            client = LettaClient()
            assert client.test_connection() is False
            mock_client.health.check.assert_called_once()

    def test_list_agents_success(self, mock_env_vars, sample_agents):
        """Test successful agent listing"""
        with patch('letta_api.LettaSDK') as mock_letta_sdk:
            mock_client = Mock()
            # Setup mock agents
            mock_agents = []
            for agent_data in sample_agents:
                mock_agent = Mock()
                mock_agent.id = agent_data["id"]
                mock_agent.name = agent_data["name"]
                mock_agent.description = agent_data["description"]
                mock_agents.append(mock_agent)

            mock_client.agents.list.return_value = mock_agents
            mock_letta_sdk.return_value = mock_client
            client = LettaClient()
            agents = client.list_agents()

            assert len(agents) == 2
            assert agents[0]["id"] == "agent_123"
            assert agents[0]["name"] == "Test Agent 1"
            assert agents[1]["id"] == "agent_456"
            assert agents[1]["name"] == "Test Agent 2"

    def test_list_agents_failure(self, mock_env_vars):
        """Test agent listing failure"""
        with patch('letta_api.LettaSDK') as mock_letta_sdk:
            mock_client = Mock()
            mock_client.agents.list.side_effect = Exception("API Error")
            mock_letta_sdk.return_value = mock_client
            client = LettaClient()
            agents = client.list_agents()
            assert agents == []

    def test_set_agent(self, mock_env_vars):
        """Test setting agent"""
        with patch('letta_api.LettaSDK') as mock_letta_sdk:
            mock_client = Mock()
            mock_letta_sdk.return_value = mock_client
            client = LettaClient()
            result = client.set_agent("new_agent_id")
            assert result is True
            assert client.current_agent_id == "new_agent_id"

    def test_send_message_success(self, mock_env_vars):
        """Test successful message sending"""
        with patch('letta_api.LettaSDK') as mock_letta_sdk:
            mock_client = Mock()
            mock_response = Mock()
            mock_message = Mock()
            mock_message.content = "Test response"
            mock_response.messages = [mock_message]
            mock_client.agents.messages.create.return_value = mock_response
            mock_letta_sdk.return_value = mock_client
            
            client = LettaClient()
            client.current_agent_id = "test_agent"
            response = client.send_message("Hello")
            assert response == "Test response"

    def test_send_message_no_agent(self, mock_env_vars):
        """Test message sending without agent"""
        with patch('letta_api.LettaSDK') as mock_letta_sdk:
            mock_client = Mock()
            mock_letta_sdk.return_value = mock_client
            client = LettaClient()
            client.current_agent_id = ""
            response = client.send_message("Hello")
            assert response is None

    def test_send_message_failure(self, mock_env_vars):
        """Test message sending failure"""
        with patch('letta_api.LettaSDK') as mock_letta_sdk:
            mock_client = Mock()
            mock_client.agents.messages.create.side_effect = Exception("API Error")
            mock_letta_sdk.return_value = mock_client
            
            client = LettaClient()
            client.current_agent_id = "test_agent"
            response = client.send_message("Hello")
            assert response is None

    @pytest.mark.asyncio
    async def test_send_message_stream_success(self, mock_env_vars):
        """Test successful streaming message"""
        with patch('letta_api.LettaSDK') as mock_letta_sdk:
            mock_client = Mock()
            mock_chunk1 = Mock()
            mock_chunk1.content = "Hello"
            mock_chunk1.message_type = "assistant_message"
            mock_chunk2 = Mock()
            mock_chunk2.content = " world!"
            mock_chunk2.message_type = "assistant_message"
            mock_client.agents.messages.create_stream.return_value = [mock_chunk1, mock_chunk2]
            mock_letta_sdk.return_value = mock_client
            
            client = LettaClient()
            client.current_agent_id = "test_agent"
            chunks = []
            async for chunk in client.send_message_stream("Hello"):
                chunks.append(chunk)
            assert chunks == ["Hello", " world!"]

    @pytest.mark.asyncio
    async def test_send_message_stream_no_agent(self, mock_env_vars):
        """Test streaming without agent"""
        with patch('letta_api.LettaSDK') as mock_letta_sdk:
            mock_client = Mock()
            mock_letta_sdk.return_value = mock_client
            client = LettaClient()
            client.current_agent_id = ""
            chunks = []
            async for chunk in client.send_message_stream("Hello"):
                chunks.append(chunk)
            assert chunks == ["Error: No agent selected"]

    @pytest.mark.asyncio
    async def test_send_message_stream_failure(self, mock_env_vars):
        """Test streaming failure"""
        with patch('letta_api.LettaSDK') as mock_letta_sdk:
            mock_client = Mock()
            mock_client.agents.messages.create_stream.side_effect = Exception("Stream Error")
            mock_letta_sdk.return_value = mock_client
            
            client = LettaClient()
            client.current_agent_id = "test_agent"
            chunks = []
            async for chunk in client.send_message_stream("Hello"):
                chunks.append(chunk)
            assert len(chunks) == 1
            assert "Error:" in chunks[0]