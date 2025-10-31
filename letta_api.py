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
import logging
from typing import List, AsyncGenerator, Optional
from letta_client import Letta as LettaSDK
from letta_client import MessageCreate
from config import config

# Configure logging
logger = logging.getLogger(__name__)

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
            # Handle SSL certificate errors gracefully
            if "CERTIFICATE_VERIFY_FAILED" in str(e) or "SSL" in str(e):
                logger.warning(f"SSL certificate verification failed: {e}")
                logger.info("Consider using a valid server URL or disabling SSL verification for development")
            else:
                logger.error(f"Connection failed: {e}")
            return False

    def list_agents(self) -> List[dict]:
        """List available agents"""
        try:
            agents = self.client.agents.list()
            return [{"id": agent.id, "name": agent.name, "description": getattr(agent, 'description', '')} for agent in agents]
        except Exception as e:
            # Handle SSL certificate errors gracefully
            if "CERTIFICATE_VERIFY_FAILED" in str(e) or "SSL" in str(e):
                logger.warning(f"SSL certificate verification failed while listing agents: {e}")
                logger.info("Consider using a valid server URL or disabling SSL verification for development")
            else:
                logger.error(f"Failed to list agents: {e}")
            return []

    def set_agent(self, agent_id: str) -> bool:
        """Set the active agent"""
        self.current_agent_id = agent_id
        return True

    def send_message(self, content: str) -> Optional[str]:
        """Send a message and get response (sync)"""
        if not self.current_agent_id:
            logger.warning("No agent selected")
            return None

        try:
            message_data = [MessageCreate(role="user", content=content)]
            response = self.client.agents.messages.create(
                agent_id=self.current_agent_id,
                messages=message_data
            )

            # Handle direct .content
            if hasattr(response, 'content') and response.content:
                return response.content

            # Handle .messages[].content
            if hasattr(response, 'messages'):
                for message in response.messages:
                    if hasattr(message, 'content') and message.content:
                        return message.content
            return None
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return None

    async def send_message_stream(self, content: str, show_reasoning: bool = False) -> AsyncGenerator[str, None]:
        """Send a message and stream response (async) with token-level streaming"""
        if not self.current_agent_id:
            yield "Error: No agent selected"
            return

        try:
            import concurrent.futures
            import queue
            
            message_data = [MessageCreate(role="user", content=content)]
            
            # Create a queue to pass chunks from thread to async loop
            chunk_queue = queue.Queue()
            
            def _stream_in_thread():
                """Run the synchronous streaming in a thread."""
                try:
                    response_stream = self.client.agents.messages.create_stream(
                        agent_id=self.current_agent_id,
                        messages=message_data,
                        stream_tokens=True
                    )
                    for chunk in response_stream:
                        chunk_queue.put(('chunk', chunk))
                    chunk_queue.put(('done', None))
                except Exception as e:
                    chunk_queue.put(('error', e))
            
            # Start streaming in a background thread
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            executor.submit(_stream_in_thread)
            
            # Read from queue and yield chunks
            while True:
                # Non-blocking queue check with timeout
                try:
                    msg_type, chunk = await asyncio.get_event_loop().run_in_executor(
                        None, chunk_queue.get, True, 0.1
                    )
                except queue.Empty:
                    continue
                
                if msg_type == 'done':
                    break
                elif msg_type == 'error':
                    yield f"Error: {chunk}"
                    break
                elif msg_type == 'chunk':
                    # Handle reasoning messages if enabled
                    reasoning_detected = False
                    
                    if show_reasoning:
                        # Inspect chunk structure - handle both object attributes and dict keys
                        message_type = None
                        if hasattr(chunk, 'message_type'):
                            message_type = chunk.message_type
                        elif isinstance(chunk, dict):
                            message_type = chunk.get('message_type')
                        
                        # Handle reasoning messages
                        if message_type == 'reasoning_message':
                            reasoning_content = None
                            if hasattr(chunk, 'reasoning'):
                                reasoning_content = chunk.reasoning
                            elif hasattr(chunk, 'content'):
                                reasoning_content = chunk.content
                            elif isinstance(chunk, dict):
                                reasoning_content = chunk.get('reasoning') or chunk.get('content')
                            
                            if reasoning_content:
                                yield f"__REASONING__:{reasoning_content}"
                                reasoning_detected = True
                        elif message_type == 'hidden_reasoning_message':
                            hidden_content = None
                            if hasattr(chunk, 'hidden_reasoning'):
                                hidden_content = chunk.hidden_reasoning
                            elif hasattr(chunk, 'content'):
                                hidden_content = chunk.content
                            elif isinstance(chunk, dict):
                                hidden_content = chunk.get('hidden_reasoning') or chunk.get('content')
                            
                            if hidden_content:
                                yield f"__REASONING__:{hidden_content}"
                                reasoning_detected = True
                    
                    # Yield content when present, but skip if it was already yielded as reasoning
                    if not reasoning_detected:
                        # Handle both object attributes and dict keys
                        content = None
                        if hasattr(chunk, 'content') and chunk.content:
                            content = chunk.content
                        elif isinstance(chunk, dict) and chunk.get('content'):
                            content = chunk.get('content')
                        
                        if content:
                            # Process literal newlines in content - convert \n to actual newlines
                            processed_content = content.replace('\\n', '\n') if isinstance(content, str) else str(content)
                            yield processed_content
            
            executor.shutdown(wait=False)

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
                    logger.error("Letta client is not available - check configuration")
                    return [] if name == 'list_agents' else None
                return unavailable_method
            raise RuntimeError("Letta client is not available - check configuration")
        return getattr(client, name)

# Create lazy client instance
letta_client = LazyLettaClient()
