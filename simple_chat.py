#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple text-based Letta chat client
Minimal interface for debugging and core functionality

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
import sys
from letta_api import letta_client
from config import config

# Configure logging conditionally
def setup_logging(verbose=False, debug=False):
    """Setup logging based on command line flags"""
    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING  # Only show warnings and errors by default
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('letta_chat.log'),
            logging.StreamHandler(sys.stdout) if verbose or debug else logging.NullHandler()
        ]
    )
    
    # Suppress verbose HTTP request logging unless debug mode
    if not debug:
        logging.getLogger('httpx').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Global state for reasoning visibility
show_reasoning = False

# Expose letta_client at module level for test patching and dependency injection
letta_client = letta_client

def safe_print(text, end="", flush=False):
    """Print text with emoji support"""
    try:
        print(text, end=end, flush=flush)
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Fallback for problematic characters
        try:
            safe_text = text.encode('utf-8', errors='replace').decode('utf-8')
            print(safe_text, end=end, flush=flush)
        except Exception:
            # Last resort - replace problematic characters
            safe_text = text.encode('ascii', errors='replace').decode('ascii')
            print(safe_text, end=end, flush=flush)

def clear_screen():
    """Clear the terminal screen - works on Windows, Unix/Linux, and Mac"""
    import os
    import sys
    
    try:
        if os.name == 'nt':  # Windows
            os.system('cls')
        else:  # Unix/Linux/Mac
            os.system('clear')
    except Exception:
        # Fallback - use ANSI escape sequence for terminals that support it
        try:
            print('\033[2J\033[H', end='', flush=True)
        except Exception:
            # Last resort - print enough newlines to clear most screens
            print('\n' * 50)

def print_banner():
    """Print a simple banner"""
    print("=" * 60)
    print("           LETTA SIMPLE CHAT CLIENT")
    print("=" * 60)
    print()

def print_status():
    """Print current status"""
    print(f"Server: {config.letta_server_url}")
    print(f"User: {config.display_name}")

    if letta_client and letta_client.current_agent_id:
        # Get agent name from the list with proper error handling
        try:
            # Check if client is available before calling methods
            if hasattr(letta_client, 'client') and letta_client.client is None:
                print(f"Agent: Unknown Agent ({letta_client.current_agent_id}) - Client not available")
            else:
                # Try to get agents list with basic error handling
                agents = letta_client.list_agents()
                agent_name = "Unknown Agent"
                
                # Validate agents list and structure
                if agents and isinstance(agents, list):
                    for agent in agents:
                        # Validate agent structure
                        if isinstance(agent, dict) and 'id' in agent and 'name' in agent:
                            if agent['id'] == letta_client.current_agent_id:
                                agent_name = agent['name']
                                break
                        else:
                            logger.warning(f"Invalid agent structure: {agent}")
                            continue
                
                print(f"Agent: {agent_name} ({letta_client.current_agent_id})")
            
        except Exception as e:
            logger.error(f"Error retrieving agent info: {e}")
            print(f"Agent: Unknown Agent ({letta_client.current_agent_id})")
    else:
        print("Agent: None selected")

def print_help():
    """Print help commands"""
    print("\nCommands:")
    print("  /help     - Show this help")
    print("  /status   - Show connection status")
    print("  /agents   - List available agents")
    print("  /agent <id> - Set agent by ID or number")
    print("  /clear    - Clear screen")
    print("  /reasoning - Toggle reasoning/thinking display")
    print("  /quit     - Exit the application")
    print("\nNote: Use /agent 5 to select agent #5 from the list")
    print("Note: Use --reasoning flag to enable reasoning by default")
    print()

async def test_connection():
    """Test connection to Letta server"""
    print("Testing connection to Letta server...")
    if letta_client.test_connection():
        print("Connected successfully!")
        return True
    else:
        print("- Connection failed!")
        return False

async def list_agents():
    """List available agents"""
    print("Fetching available agents...")
    agents = letta_client.list_agents()
    if agents:
        print(f"Found {len(agents)} agents:")
        for i, agent in enumerate(agents, 1):
            print(f"  {i}. {agent['name']} (ID: {agent['id']})")
            if agent['description']:
                print(f"      {agent['description']}")
    else:
        print("No agents found or error occurred")
    print()

async def set_agent(agent_id: str):
    """Set the active agent by ID or number"""
    # Check if it's a number (from the list)
    if agent_id.isdigit():
        agents = letta_client.list_agents()
        try:
            agent_index = int(agent_id) - 1  # Convert to 0-based index
            if 0 <= agent_index < len(agents):
                actual_agent_id = agents[agent_index]['id']
                if letta_client.set_agent(actual_agent_id):
                    print(f"Set agent: {agents[agent_index]['name']} (ID: {actual_agent_id})")
                else:
                    print(f"Failed to set agent: {agent_id}")
            else:
                print(f"Invalid agent number: {agent_id}. Use /agents to see available agents.")
        except (ValueError, IndexError):
            print(f"Invalid agent number: {agent_id}. Use /agents to see available agents.")
    else:
        # Try as direct agent ID
        if letta_client.set_agent(agent_id):
            print(f"Set agent: {agent_id}")
        else:
            print(f"Failed to set agent: {agent_id}")
    print()

async def send_message(message: str):
    """Send a message to the agent"""
    if not message.strip():
        return

    # Get the current agent name for display
    agent_name = "Assistant"  # Default fallback
    if letta_client and letta_client.current_agent_id:
        try:
            agents = letta_client.list_agents()
            if agents and isinstance(agents, list):
                for agent in agents:
                    if isinstance(agent, dict) and 'id' in agent and 'name' in agent:
                        if agent['id'] == letta_client.current_agent_id:
                            agent_name = agent['name']
                            break
        except Exception:
            # If we can't get the agent name, fall back to "Assistant"
            pass
    
    print(f"[{agent_name}] ", end="", flush=True)

    try:
        # Use streaming for real-time response
        response = ""
        async for chunk in letta_client.send_message_stream(message, show_reasoning=show_reasoning):
            safe_print(chunk, end="", flush=True)
            response += chunk

        print()  # New line after response

    except Exception as e:
        print(f"Error: {e}")

async def main(verbose=False, debug=False, reasoning=False):
    """Main application loop"""
    # Setup logging first
    setup_logging(verbose=verbose, debug=debug)
    
    # Set global state for reasoning display
    global show_reasoning
    show_reasoning = reasoning
    
    print_banner()

    # Validate configuration
    if not config.validate():
        print("Configuration validation failed. Please check your .env file.")
        return

    # Test connection
    if not await test_connection():
        print("Cannot connect to server. Exiting.")
        return

    # List agents
    await list_agents()

    # Set agent if configured
    if config.default_agent_id:
        await set_agent(config.default_agent_id)

    print_status()
    print_help()

    # Main chat loop
    while True:
        try:
            user_input = input(f"\n[{config.display_name}] ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.startswith('/'):
                parts = user_input[1:].split(' ', 1)
                command = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else ""

                if command == 'help':
                    print_help()
                elif command == 'status':
                    print_status()
                elif command == 'agents':
                    await list_agents()
                elif command == 'agent':
                    if arg:
                        await set_agent(arg)
                    else:
                        print("Usage: /agent <agent_id>")
                elif command == 'clear':
                    clear_screen()
                elif command == 'reasoning':
                    show_reasoning = not show_reasoning
                    print(f"Reasoning display: {'ON' if show_reasoning else 'OFF'}")
                elif command == 'quit':
                    print("Goodbye!")
                    break
                else:
                    print(f"Unknown command: {command}")
                    print_help()
            else:
                # Send message
                await send_message(user_input)

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except EOFError:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main())
