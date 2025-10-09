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
from typing import List, AsyncGenerator, Optional
from letta_client import Letta as LettaSDK
from letta_client import MessageCreate
from config import config

class LettaClient:
    """Simple Letta API client"""

    def __init__(self):
        # Create client with proper configuration
        self.client = LettaSDK(
            base_url=config.letta_server_url,
            token=config.letta_api_token
        )
        self.current_agent_id = config.default_agent_id or ""

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

            # Extract content from the response messages
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
            yield "Error: No agent selected"
            return

        try:
            message_data = [MessageCreate(role="user", content=content)]
            response_stream = self.client.agents.messages.create_stream(
                agent_id=self.current_agent_id,
                messages=message_data,
                stream_tokens=True  # Enable token-level streaming
            )

            for chunk in response_stream:
                # Only yield content from AssistantMessage chunks
                if (hasattr(chunk, 'content') and
                    chunk.content and
                    hasattr(chunk, 'message_type') and
                    chunk.message_type == 'assistant_message'):
                    yield chunk.content

        except Exception as e:
            yield f"Error: {e}"

# Global client instance - lazy initialization
_letta_client = None

class LazyLettaClient:
    """Lazy initialization wrapper for LettaClient"""
    
    def __init__(self):
        self._client = None
    
    def _ensure_client(self):
        """Ensure client is initialized"""
        global _letta_client
        if _letta_client is None:
            try:
                if config.validate():
                    _letta_client = LettaClient()
                else:
                    _letta_client = None
            except Exception as e:
                _letta_client = None
        self._client = _letta_client
        return self._client
    
    def __getattr__(self, name):
        """Delegate attribute access to the actual client"""
        client = self._ensure_client()
        if client is None:
            # Return None for common attributes when client is not available
            if name in ['current_agent_id', 'client']:
                return None
            # For method calls, return a function that handles the unavailable state
            if callable(getattr(LettaClient, name, None)):
                def unavailable_method(*args, **kwargs):
                    print(f"Letta client is not available - check configuration")
                    return [] if name == 'list_agents' else None
                return unavailable_method
            raise RuntimeError("Letta client is not available - check configuration")
        return getattr(client, name)

# Create lazy client instance
letta_client = LazyLettaClient()
