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
        with patch.dict(os.environ, {}, clear=True):
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
        with patch.dict(os.environ, {"LETTA_SERVER_URL": "https://test.com"}, clear=True):
            config = Config()
            assert config.validate() is False
    
    def test_validate_missing_server_url(self):
        """Test validation with missing server URL"""
        with patch.dict(os.environ, {"LETTA_API_TOKEN": "token"}, clear=True):
            config = Config()
            assert config.validate() is False
    
    def test_validate_default_server_url(self):
        """Test validation with default server URL"""
        with patch.dict(os.environ, {"LETTA_API_TOKEN": "token"}, clear=True):
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

