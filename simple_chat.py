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
import sys
from letta_api import letta_client
from config import config

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
        # Get agent name from the list
        agents = letta_client.list_agents()
        agent_name = "Unknown Agent"
        for agent in agents:
            if agent['id'] == letta_client.current_agent_id:
                agent_name = agent['name']
                break
        print(f"Agent: {agent_name} ({letta_client.current_agent_id})")
    else:
        print("Agent: None selected")
    
    print("-" * 60)

def print_help():
    """Print help commands"""
    print("\nCommands:")
    print("  /help     - Show this help")
    print("  /status   - Show connection status")
    print("  /agents   - List available agents")
    print("  /agent <id> - Set agent by ID or number")
    print("  /clear    - Clear screen")
    print("  /quit     - Exit the application")
    print("\nNote: Use /agent 5 to select agent #5 from the list")
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
    
    print(f"\n[You] {message}")
    print("[Assistant] ", end="", flush=True)
    
    try:
        # Use streaming for real-time response
        response = ""
        async for chunk in letta_client.send_message_stream(message):
            safe_print(chunk, end="", flush=True)
            response += chunk
        
        print()  # New line after response
        
    except Exception as e:
        print(f"Error: {e}")

async def main():
    """Main application loop"""
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
                    print("\n" + "=" * 60)
                    print("Screen cleared")
                    print("=" * 60)
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
