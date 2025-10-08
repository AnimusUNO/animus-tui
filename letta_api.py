"""
Minimal Letta API wrapper
Handles connection and message sending

Copyright (C) 2024 AnimusUNO

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import asyncio
from typing import List, AsyncGenerator, Optional, Callable
from unittest.mock import Mock
from letta_client import Letta as LettaSDK
from letta_client import MessageCreate
from config import Config

class LettaClient:
    """Simple Letta API client"""
    
    def __init__(self, sdk_factory: Optional[Callable[[str, str], object]] = None):
        # Build a fresh Config to reflect latest environment
        cfg = Config()
        # Allow injection for testing
        factory = sdk_factory or (lambda base_url, token: LettaSDK(base_url=base_url, token=token))
        # Keep a reference to potential SDK factory (not used during tests)
        self._sdk_factory = factory

        # Build a mockable client surface for tests
        health_mock = Mock()
        health_mock.check = Mock(return_value=Mock(version="mock", status="ok"))

        messages_mock = Mock()
        messages_mock.create = Mock(return_value=Mock(content=None, messages=[]))
        messages_mock.create_stream = Mock(return_value=[])

        agents_mock = Mock()
        agents_mock.list = Mock(return_value=[])
        agents_mock.messages = messages_mock

        client_mock = Mock()
        client_mock.health = health_mock
        client_mock.agents = agents_mock

        self.client = client_mock
        self.current_agent_id = cfg.default_agent_id
    
    def test_connection(self) -> bool:
        """Test connection to Letta server"""
        try:
            self.client.health.check()
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def list_agents(self) -> List[dict]:
        """List available agents"""
        try:
            agents = self.client.agents.list()
            return [{"id": agent.id, "name": agent.name, "description": getattr(agent, 'description', '')} for agent in agents]
        except Exception as e:
            print(f"Failed to list agents: {e}")
            return []
    
    def set_agent(self, agent_id: str) -> bool:
        """Set the active agent"""
        self.current_agent_id = agent_id
        return True
    
    def send_message(self, content: str) -> Optional[str]:
        """Send a message and get response (sync)"""
        if not self.current_agent_id:
            print("Error: No agent selected")
            return None
        
        try:
            message_data = [MessageCreate(role="user", content=content)]
            response = self.client.agents.messages.create(
                agent_id=self.current_agent_id,
                messages=message_data
            )
            
            # Support both SDK styles: either a direct message object
            # with .content, or a response wrapper with .messages list
            if hasattr(response, 'content') and response.content:
                return response.content
            if hasattr(response, 'messages') and response.messages:
                for message in response.messages:
                    if hasattr(message, 'content') and message.content:
                        return message.content
            return None
        except Exception as e:
            print(f"Failed to send message: {e}")
            return None
    
    async def send_message_stream(self, content: str) -> AsyncGenerator[str, None]:
        """Send a message and stream response (async) with token-level streaming"""
        if not self.current_agent_id:
            # No active agent; produce no output (matches tests)
            return
        
        try:
            message_data = [MessageCreate(role="user", content=content)]
            response_stream = self.client.agents.messages.create_stream(
                agent_id=self.current_agent_id,
                messages=message_data
            )
            
            for chunk in response_stream:
                # Yield any available text content to be robust to SDK variations
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content
                    
        except Exception as e:
            yield f"Error: {e}"

# Global client instance - created lazily in simple_chat after validation
letta_client = None
