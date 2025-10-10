"""
Unit tests for config.py
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open
from config import Config

class TestConfig:
    def test_initialization_defaults(self):
        """Test config initialization with defaults"""
        with patch.dict(os.environ, {}, clear=True), \
             patch('config.load_dotenv'):
            config = Config()
            assert config.letta_server_url == "https://your-letta-server.com:8283"
            assert config.letta_api_token == ""
            assert config.display_name == "User"
            assert config.default_agent_id == ""

    def test_initialization_from_env(self, mock_env_vars):
        """Test config initialization from environment variables"""
        config = Config()
        assert config.letta_server_url == "https://test-server.com:8283"
        assert config.letta_api_token == "test_token_123"
        assert config.display_name == "TestUser"
        assert config.default_agent_id == "agent_123"

    def test_validate_success(self, mock_env_vars):
        """Test successful validation"""
        config = Config()
        assert config.validate() is True

    def test_validate_missing_token(self):
        """Test validation with missing API token"""
        with patch.dict(os.environ, {"LETTA_SERVER_URL": "https://test.com"}, clear=True), \
             patch('config.load_dotenv'):
            config = Config()
            assert config.validate() is False

    def test_validate_missing_server_url(self):
        """Test validation with missing server URL"""
        with patch.dict(os.environ, {"LETTA_API_TOKEN": "token"}, clear=True), \
             patch('config.load_dotenv'):
            config = Config()
            assert config.validate() is False

    def test_validate_default_server_url(self):
        """Test validation with default server URL"""
        with patch.dict(os.environ, {"LETTA_API_TOKEN": "token"}, clear=True), \
             patch('config.load_dotenv'):
            config = Config()
            assert config.validate() is False

    def test_get_letta_client_config(self, mock_env_vars):
        """Test getting Letta client configuration"""
        config = Config()
        client_config = config.get_letta_client_config()

        expected = {
            "base_url": "https://test-server.com:8283",
            "token": "test_token_123"
        }
        assert client_config == expected

    def test_save_to_env_new_file(self):
        """Test saving to new .env file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"

            with patch('config.Path', return_value=env_path):
                config = Config()
                config.save_to_env(
                    LETTA_SERVER_URL="https://new-server.com",
                    LETTA_API_TOKEN="new_token"
                )

                assert env_path.exists()
                content = env_path.read_text()
                assert "LETTA_SERVER_URL=https://new-server.com" in content
                assert "LETTA_API_TOKEN=new_token" in content
                assert "# Letta Chat Client Configuration" in content

    def test_save_to_env_existing_file(self):
        """Test saving to existing .env file (idempotent)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"

            # Create existing .env file
            env_path.write_text("""# Existing config
LETTA_SERVER_URL=https://old-server.com
DISPLAY_NAME=OldUser
""")

            with patch('config.Path', return_value=env_path):
                config = Config()
                config.save_to_env(
                    LETTA_SERVER_URL="https://new-server.com",
                    LETTA_API_TOKEN="new_token"
                )

                content = env_path.read_text()
                assert "LETTA_SERVER_URL=https://new-server.com" in content
                assert "LETTA_API_TOKEN=new_token" in content
                assert "DISPLAY_NAME=OldUser" in content  # Should preserve existing

    def test_save_to_env_idempotent(self):
        """Test that save_to_env is idempotent"""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"

            with patch('config.Path', return_value=env_path):
                config = Config()

                # Save first time
                config.save_to_env(LETTA_SERVER_URL="https://test.com")

                # Save second time with same data
                config.save_to_env(LETTA_SERVER_URL="https://test.com")

                # Should not duplicate
                content = env_path.read_text()
                assert content.count("LETTA_SERVER_URL=https://test.com") == 1

class TestConfigInteractiveFunctions:
    """Test interactive configuration functions"""
    
    def test_get_user_input_with_default(self):
        """Test get_user_input with default value"""
        from config import get_user_input
        from unittest.mock import patch
        
        with patch('builtins.input', return_value=''):
            result = get_user_input("Enter value", default="default_value")
            assert result == "default_value"
    
    def test_get_user_input_with_user_input(self):
        """Test get_user_input with user input"""
        from config import get_user_input
        from unittest.mock import patch
        
        with patch('builtins.input', return_value='user_value'):
            result = get_user_input("Enter value", default="default_value")
            assert result == "user_value"
    
    def test_get_user_input_required_empty(self):
        """Test get_user_input with required field and empty input"""
        from config import get_user_input
        from unittest.mock import patch
        
        with patch('builtins.input', side_effect=['', 'valid_value']):
            result = get_user_input("Enter value", required=True)
            assert result == "valid_value"
    
    def test_get_user_input_not_required(self):
        """Test get_user_input with not required field"""
        from config import get_user_input
        from unittest.mock import patch
        
        with patch('builtins.input', return_value=''):
            result = get_user_input("Enter value", required=False)
            assert result == ""
    
    def test_test_letta_connection_success(self):
        """Test successful Letta connection"""
        from config import test_letta_connection
        from unittest.mock import patch, Mock
        
        mock_client = Mock()
        mock_client.health.check.return_value = None
        
        with patch('letta_client.Letta', return_value=mock_client):
            success, message = test_letta_connection("https://test.com", "token")
            assert success is True
            assert message == "Connection successful"
    
    def test_test_letta_connection_failure(self):
        """Test failed Letta connection"""
        from config import test_letta_connection
        from unittest.mock import patch, Mock
        
        mock_client = Mock()
        mock_client.health.check.side_effect = Exception("Connection failed")
        
        with patch('letta_client.Letta', return_value=mock_client):
            success, message = test_letta_connection("https://test.com", "token")
            assert success is False
            assert message == "Connection failed"
    
    def test_get_available_agents_success(self):
        """Test getting available agents successfully"""
        from config import get_available_agents
        from unittest.mock import patch, Mock
        
        mock_client = Mock()
        mock_agent1 = Mock()
        mock_agent1.id = "agent1"
        mock_agent1.name = "Agent 1"
        mock_agent1.description = "Test agent 1"
        
        mock_agent2 = Mock()
        mock_agent2.id = "agent2"
        mock_agent2.name = "Agent 2"
        # No description attribute - use getattr to return empty string
        mock_agent2.description = ""
        
        mock_client.agents.list.return_value = [mock_agent1, mock_agent2]
        
        with patch('letta_client.Letta', return_value=mock_client):
            agents = get_available_agents("https://test.com", "token")
            assert len(agents) == 2
            assert agents[0] == {"id": "agent1", "name": "Agent 1", "description": "Test agent 1"}
            assert agents[1] == {"id": "agent2", "name": "Agent 2", "description": ""}
    
    def test_get_available_agents_failure(self):
        """Test getting available agents with error"""
        from config import get_available_agents
        from unittest.mock import patch, Mock
        
        mock_client = Mock()
        mock_client.agents.list.side_effect = Exception("API Error")
        
        with patch('letta_client.Letta', return_value=mock_client):
            agents = get_available_agents("https://test.com", "token")
            assert agents == []
    
    def test_interactive_setup_cancelled(self):
        """Test interactive setup when user cancels"""
        from config import interactive_setup
        from unittest.mock import patch
        
        with patch('config.get_user_input', side_effect=['https://test.com', 'token']), \
             patch('config.test_letta_connection', return_value=(False, "Connection failed")), \
             patch('builtins.input', return_value='n'):  # User chooses not to retry
            
            result = interactive_setup()
            assert result is False
    
    def test_interactive_setup_success(self):
        """Test successful interactive setup"""
        from config import interactive_setup
        from unittest.mock import patch
        
        with patch('config.get_user_input', side_effect=[
            'https://test.com',  # server URL
            'token',            # API token
            'TestUser'          # display name
        ]), \
        patch('config.test_letta_connection', return_value=(True, "Success")), \
        patch('config.get_available_agents', return_value=[]), \
        patch('config.Config.save_to_env'):
            
            result = interactive_setup()
            assert result is True

