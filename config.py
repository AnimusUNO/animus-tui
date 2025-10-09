"""
Configuration management for Letta Chat Client
Loads settings from environment variables - idempotent

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
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
# load_dotenv()  # Moved to Config.__init__ to avoid import-time side effects

class Config:
    """Configuration settings - idempotent"""

    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        self.letta_server_url = os.getenv("LETTA_SERVER_URL", "https://your-letta-server.com:8283")
        self.letta_api_token = os.getenv("LETTA_API_TOKEN", "")
        self.display_name = os.getenv("DISPLAY_NAME", "User")
        self.default_agent_id = os.getenv("DEFAULT_AGENT_ID", "")

    def validate(self) -> bool:
        """Validate required configuration"""
        if not self.letta_api_token:
            logger.error("LETTA_API_TOKEN is required")
            return False

        if not self.letta_server_url or self.letta_server_url == "https://your-letta-server.com:8283":
            logger.error("LETTA_SERVER_URL must be set to your actual server")
            return False

        return True

    def get_letta_client_config(self) -> dict:
        """Get configuration for Letta client"""
        return {
            "base_url": self.letta_server_url,
            "token": self.letta_api_token
        }

    def save_to_env(self, **kwargs) -> None:
        """Save configuration to .env file - idempotent"""
        env_path = Path(".env")

        # Read existing .env if it exists
        existing_vars = {}
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        existing_vars[key] = value

        # Update with new values
        existing_vars.update(kwargs)

        # Write back to .env
        with open(env_path, 'w') as f:
            f.write("# Letta Chat Client Configuration\n")
            f.write("# Generated automatically - safe to edit\n\n")
            for key, value in existing_vars.items():
                # Quote values that contain spaces, #, or =
                if any(char in str(value) for char in [' ', '#', '=']):
                    f.write(f'{key}="{value}"\n')
                else:
                    f.write(f"{key}={value}\n")
        
        # Set secure permissions on POSIX systems
        if hasattr(os, 'chmod'):
            os.chmod(env_path, 0o600)  # Read/write for owner only

# Global config instance
config = Config()

def get_user_input(prompt, default=None, required=True):
    """Get user input with optional default value"""
    while True:
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            if not user_input:
                user_input = default
        else:
            user_input = input(f"{prompt}: ").strip()

        if user_input or not required:
            return user_input
        print("This field is required. Please enter a value.")

def test_letta_connection(server_url, api_token):
    """Test connection to Letta server"""
    try:
        from letta_client import Letta as LettaClient
        test_client = LettaClient(base_url=server_url, token=api_token)
        test_client.health.check()
        return True, "Connection successful"
    except Exception as e:
        return False, str(e)

def get_available_agents(server_url, api_token):
    """Get list of available agents from server"""
    try:
        from letta_client import Letta as LettaClient
        client = LettaClient(base_url=server_url, token=api_token)
        agents = client.agents.list()
        return [{"id": agent.id, "name": agent.name, "description": getattr(agent, 'description', '')} for agent in agents]
    except Exception as e:
        print(f"Error fetching agents: {e}")
        return []

def interactive_setup():
    """Interactive configuration setup"""
    print("Letta Chat Client - Interactive Setup")
    print("=" * 40)
    print("This will help you configure your Letta chat client.")
    print()

    # Get server URL
    print("1. Letta Server Configuration")
    server_url = get_user_input("Enter your Letta server URL", "https://your-letta-server.com:8283")

    # Get API token
    print()
    print("2. Authentication")
    api_token = get_user_input("Enter your API token", required=True)

    # Test connection
    print()
    print("3. Testing Connection")
    print("Testing connection to Letta server...")
    success, message = test_letta_connection(server_url, api_token)

    if not success:
        print(f"[ERROR] Connection failed: {message}")
        retry = input("Do you want to try again? (y/n): ").strip().lower()
        if retry == 'y':
            return interactive_setup()
        else:
            print("Setup cancelled.")
            return False

    print("[OK] Connection successful!")

    # Get display name
    print()
    print("4. User Configuration")
    display_name = get_user_input("Enter your display name", "User")

    # Get available agents and let user select
    print()
    print("5. Agent Selection")
    print("Fetching available agents...")
    agents = get_available_agents(server_url, api_token)

    default_agent_id = ""
    if agents:
        print(f"Found {len(agents)} available agents:")
        for i, agent in enumerate(agents, 1):
            print(f"  {i}. {agent['name']} (ID: {agent['id']})")
            if agent['description']:
                print(f"      {agent['description']}")

        print()
        while True:
            choice = input("Select default agent (number or ID, or press Enter to skip): ").strip()
            if not choice:
                break

            # Try to parse as number
            try:
                agent_num = int(choice)
                if 1 <= agent_num <= len(agents):
                    default_agent_id = agents[agent_num - 1]['id']
                    print(f"Selected: {agents[agent_num - 1]['name']}")
                    break
                else:
                    print(f"Please enter a number between 1 and {len(agents)}")
            except ValueError:
                # Try to find by ID
                found = False
                for agent in agents:
                    if agent['id'] == choice:
                        default_agent_id = choice
                        print(f"Selected: {agent['name']}")
                        found = True
                        break
                if found:
                    break
                else:
                    print(f"Agent ID '{choice}' not found. Please try again.")
    else:
        print("No agents found. You can set an agent later.")

    # Save configuration
    print()
    print("6. Saving Configuration")
    config.save_to_env(
        LETTA_SERVER_URL=server_url,
        LETTA_API_TOKEN=api_token,
        DISPLAY_NAME=display_name,
        DEFAULT_AGENT_ID=default_agent_id
    )

    print("[OK] Configuration saved to .env file")
    print()
    print("Setup complete! You can now run the chat client with:")
    print("  python simple_chat.py")

    return True

def main():
    """Main function for standalone execution"""
    print("Letta Chat Client - Configuration Setup")
    print("=" * 40)

    # Check if .env exists
    env_path = Path(".env")
    if env_path.exists():
        print("[OK] .env file found")
        print(f"Current configuration:")
        print(f"  Server URL: {config.letta_server_url}")
        print(f"  Display Name: {config.display_name}")
        print(f"  Default Agent: {config.default_agent_id or 'None'}")
        print(f"  API Token: {'Set' if config.letta_api_token else 'Not set'}")

        if config.validate():
            print("[OK] Configuration is valid")
            print()
            reconfigure = input("Do you want to reconfigure? (y/n): ").strip().lower()
            if reconfigure == 'y':
                return interactive_setup()
        else:
            print("[ERROR] Configuration validation failed")
            print("Starting interactive setup...")
            print()
            return interactive_setup()
    else:
        print("[ERROR] .env file not found")
        print("Starting interactive setup...")
        print()
        return interactive_setup()

if __name__ == "__main__":
    main()
