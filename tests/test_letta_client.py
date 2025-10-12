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
        with patch('letta_api.config') as mock_config, \
             patch('letta_api.LettaSDK') as mock_sdk_class:
            mock_config.default_agent_id = "agent_123"
            mock_config.letta_server_url = "https://test-server.com:8283"
            mock_config.letta_api_token = "test_token_123"
            
            # Create a mock SDK instance
            mock_sdk = Mock()
            mock_sdk_class.return_value = mock_sdk
            
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

    def test_send_message_success_direct_content(self, client):
        """Test successful message sending with direct response.content"""
        client.current_agent_id = "agent_123"
        mock_response = Mock()
        mock_response.content = "Direct response"
        mock_response.messages = []  # Empty messages array
        client.client.agents.messages.create.return_value = mock_response

        response = client.send_message("Hello")

        assert response == "Direct response"
        client.client.agents.messages.create.assert_called_once_with(
            agent_id="agent_123",
            messages=[MessageCreate(role="user", content="Hello")]
        )

    def test_send_message_success(self, client):
        """Test successful message sending"""
        client.current_agent_id = "agent_123"
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = "Test response"
        mock_response.messages = [mock_message]
        # Ensure response.content is None so it falls back to messages
        mock_response.content = None
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

    def test_send_message_stream_content_only(self, client):
        """Test streaming with content-only chunks (no message_type dependency)"""
        client.current_agent_id = "agent_123"

        # Mock streaming response with chunks that have content but no message_type
        mock_chunk1 = Mock()
        mock_chunk1.content = "Hello "
        # No message_type attribute - this should still work with our fix
        
        mock_chunk2 = Mock()
        mock_chunk2.content = "world!"
        # No message_type attribute - this should still work with our fix

        client.client.agents.messages.create_stream.return_value = [mock_chunk1, mock_chunk2]

        # Test the streaming logic synchronously by calling the generator
        stream_gen = client.send_message_stream("Hello")
        
        # Since it's async, we'll test the logic by checking the mock calls
        client.client.agents.messages.create_stream.assert_not_called()
        
        # The method should be called when we iterate
        import asyncio
        async def test_stream():
            chunks = []
            async for chunk in client.send_message_stream("Hello"):
                chunks.append(chunk)
            return chunks
        
        chunks = asyncio.run(test_stream())
        assert chunks == ["Hello ", "world!"]
        client.client.agents.messages.create_stream.assert_called_once_with(
            agent_id="agent_123",
            messages=[MessageCreate(role="user", content="Hello")],
            stream_tokens=True
        )

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
            messages=[MessageCreate(role="user", content="Hello")],
            stream_tokens=True
        )

    @pytest.mark.asyncio
    async def test_send_message_stream_no_agent(self, client):
        """Test streaming with no agent selected"""
        client.current_agent_id = None

        chunks = []
        async for chunk in client.send_message_stream("Hello"):
            chunks.append(chunk)

        assert chunks == ["Error: No agent selected"]
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

    def test_test_connection_ssl_error(self, client):
        """Test connection with SSL certificate error"""
        client.client.health.check.side_effect = Exception("CERTIFICATE_VERIFY_FAILED: certificate verify failed")
        
        result = client.test_connection()
        assert result is False

    def test_list_agents_ssl_error(self, client):
        """Test list agents with SSL certificate error"""
        client.client.agents.list.side_effect = Exception("SSL certificate verification failed")
        
        result = client.list_agents()
        assert result == []

    def test_send_message_exception(self, client):
        """Test send_message with exception"""
        client.current_agent_id = "agent_123"
        client.client.agents.messages.create.side_effect = Exception("API Error")

        response = client.send_message("Hello")
        assert response is None

    @pytest.mark.asyncio
    async def test_send_message_stream_reasoning(self, client):
        """Test streaming with reasoning messages"""
        client.current_agent_id = "agent_123"

        # Mock reasoning chunk
        mock_reasoning_chunk = Mock()
        mock_reasoning_chunk.message_type = "reasoning_message"
        mock_reasoning_chunk.reasoning = "I need to think about this"
        mock_reasoning_chunk.content = None

        # Mock content chunk
        mock_content_chunk = Mock()
        mock_content_chunk.content = "Here's my response"
        mock_content_chunk.message_type = None

        client.client.agents.messages.create_stream.return_value = [mock_reasoning_chunk, mock_content_chunk]

        chunks = []
        async for chunk in client.send_message_stream("Hello", show_reasoning=True):
            chunks.append(chunk)

        assert "__REASONING__:I need to think about this" in chunks
        assert "Here's my response" in chunks

    @pytest.mark.asyncio
    async def test_send_message_stream_hidden_reasoning(self, client):
        """Test streaming with hidden reasoning messages"""
        client.current_agent_id = "agent_123"

        # Mock hidden reasoning chunk
        mock_hidden_chunk = Mock()
        mock_hidden_chunk.message_type = "hidden_reasoning_message"
        mock_hidden_chunk.hidden_reasoning = "Secret thoughts"
        mock_hidden_chunk.content = None

        client.client.agents.messages.create_stream.return_value = [mock_hidden_chunk]

        chunks = []
        async for chunk in client.send_message_stream("Hello", show_reasoning=True):
            chunks.append(chunk)

        assert "[Hidden Thinking] Secret thoughts" in chunks

class TestLazyLettaClient:
    """Test LazyLettaClient functionality"""
    
    def test_lazy_client_unavailable(self):
        """Test LazyLettaClient when client is unavailable"""
        from letta_api import LazyLettaClient
        from unittest.mock import patch
        
        # Mock config validation to fail
        with patch('letta_api.config.validate', return_value=False):
            lazy_client = LazyLettaClient()
            
            # Test that methods return appropriate defaults when unavailable
            assert lazy_client.test_connection() is None
            assert lazy_client.list_agents() == []
            assert lazy_client.set_agent("test") is None
            assert lazy_client.send_message("test") is None
    
    @pytest.mark.asyncio
    async def test_lazy_client_stream_unavailable(self):
        """Test LazyLettaClient streaming when unavailable"""
        from letta_api import LazyLettaClient
        from unittest.mock import patch
        
        # Mock config validation to fail
        with patch('letta_api.config.validate', return_value=False):
            lazy_client = LazyLettaClient()
            
            # When client is unavailable, send_message_stream returns None
            stream = lazy_client.send_message_stream("test")
            assert stream is None
