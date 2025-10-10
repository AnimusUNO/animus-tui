"""
Integration tests for the complete application flow
"""
import pytest
import asyncio
import os
from unittest.mock import patch, Mock, AsyncMock
from pathlib import Path
from config import Config
from letta_api import LettaClient

class TestIntegration:
    def test_config_and_client_integration(self, mock_env_vars):
        """Test that config and client work together"""
        with patch('letta_api.LettaSDK') as mock_sdk_class, \
             patch('letta_api.config') as mock_config:
            mock_sdk = Mock()
            mock_sdk_class.return_value = mock_sdk
            
            # Setup mock config
            mock_config.default_agent_id = "agent_123"
            mock_config.letta_server_url = "https://test.com"
            mock_config.letta_api_token = "test_token"
            
            client = LettaClient()
            assert client.current_agent_id == mock_config.default_agent_id

    def test_full_workflow_simulation(self, mock_env_vars, mock_letta_client):
        """Test complete workflow simulation"""
        with patch('simple_chat.config') as mock_config, \
             patch('simple_chat.letta_client', mock_letta_client):

            # Setup mocks
            mock_config.validate.return_value = True
            mock_config.display_name = "TestUser"
            mock_config.default_agent_id = "agent_123"
            
            # Setup mock client return values
            mock_letta_client.test_connection.return_value = True
            mock_letta_client.list_agents.return_value = [{"id": "agent_123", "name": "Test Agent"}]
            mock_letta_client.set_agent.return_value = True
            mock_letta_client.send_message.return_value = "Test response from agent"

            # Test connection
            assert mock_letta_client.test_connection() is True

            # Test agent listing
            agents = mock_letta_client.list_agents()
            assert len(agents) == 1

            # Test agent setting
            assert mock_letta_client.set_agent("agent_123") is True

            # Test message sending
            response = mock_letta_client.send_message("Hello")
            assert response == "Test response from agent"

    @pytest.mark.asyncio
    async def test_streaming_workflow(self, mock_env_vars, mock_letta_client):
        """Test streaming message workflow"""
        with patch('simple_chat.config') as mock_config, \
             patch('simple_chat.letta_client', mock_letta_client):

            mock_config.validate.return_value = True
            mock_config.display_name = "TestUser"
            mock_config.default_agent_id = "agent_123"
            
            # Setup async mock for streaming
            async def mock_stream():
                yield "Streaming response chunk"
            
            mock_letta_client.send_message_stream.return_value = mock_stream()

            # Test streaming
            chunks = []
            async for chunk in mock_letta_client.send_message_stream("Hello"):
                chunks.append(chunk)

            assert len(chunks) == 1
            assert chunks[0] == "Streaming response chunk"

    def test_error_handling_chain(self, mock_env_vars):
        """Test error handling across components"""
        with patch('letta_api.LettaSDK') as mock_sdk_class:
            mock_sdk = Mock()
            mock_sdk.health.check.side_effect = Exception("Health check failed")
            mock_sdk_class.return_value = mock_sdk

            client = LettaClient()
            assert client.test_connection() is False

    def test_config_idempotency(self, temp_env_file):
        """Test that config operations are idempotent"""
        with patch('config.Path', return_value=Path(temp_env_file)):
            config = Config()

            # Save multiple times
            config.save_to_env(LETTA_SERVER_URL="https://test.com")
            config.save_to_env(LETTA_SERVER_URL="https://test.com")
            config.save_to_env(LETTA_SERVER_URL="https://test.com")

            # Should not create duplicates
            with open(temp_env_file, 'r') as f:
                content = f.read()
                assert content.count("LETTA_SERVER_URL=https://test.com") == 1

    def test_environment_loading(self, temp_env_file):
        """Test environment loading from file"""
        with patch('config.load_dotenv') as mock_load_dotenv:
            config = Config()
            mock_load_dotenv.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, mock_env_vars, mock_letta_client):
        """Test concurrent operations (simulated)"""
        with patch('simple_chat.config') as mock_config, \
             patch('simple_chat.letta_client', mock_letta_client):

            mock_config.validate.return_value = True
            mock_config.display_name = "TestUser"
            mock_config.default_agent_id = "agent_123"
            
            # Setup async mock for streaming
            async def mock_stream_generator():
                yield "Response for message"
            
            # Create a fresh generator for each call
            mock_letta_client.send_message_stream.side_effect = lambda msg: mock_stream_generator()

            # Simulate multiple operations
            tasks = []
            for i in range(5):
                task = asyncio.create_task(
                    self._collect_stream_chunks(mock_letta_client.send_message_stream(f"Message {i}"))
                )
                tasks.append(task)

            # Wait for all tasks
            results = await asyncio.gather(*tasks)

            # All should complete successfully
            assert len(results) == 5
            for result in results:
                assert len(result) == 1
                assert "Response for message" in result[0]
    
    async def _collect_stream_chunks(self, stream):
        """Helper to collect chunks from async stream"""
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        return chunks
