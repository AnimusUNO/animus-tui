#!/usr/bin/env python3
"""
Enhanced TUI Chat Interface
Maps beautiful UI to existing animus-chat functionality

Copyright (C) 2024 AnimusUNO
"""
import os
import sys
import asyncio
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Static, Input, Footer, Markdown
from textual.binding import Binding
from textual.message import Message
from rich.text import Text
from rich.console import Console

# Import the existing backend functionality
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config
from letta_api import letta_client

# Import our UI theme
from theme import get_palette


@dataclass
class ChatTurn:
    role: str
    content: str
    timestamp: datetime
    agent_name: str = None


class ChatTranscript(ScrollableContainer):
    """Enhanced chat display that preserves backend functionality."""

    def __init__(self) -> None:
        super().__init__()
        self._turns: List[ChatTurn] = []
        self._content_widget = Static("", id="chat_content")
        self._show_welcome = True
        self.can_focus = True

    def compose(self) -> ComposeResult:
        yield self._content_widget

    def clear(self) -> None:
        self._turns.clear()
        self._content_widget.update("")
        self._show_welcome = True
        self.refresh()

    def append(self, role: str, content: str, agent_name: str = None) -> None:
        """Add a new message turn."""
        # Store agent name with the turn for display
        turn = ChatTurn(role=role, content=content, timestamp=datetime.now())
        if agent_name and role == "agent":
            turn.agent_name = agent_name
        self._turns.append(turn)
        self._show_welcome = False
        self._render_turns()
        # Auto-scroll to bottom
        self.scroll_end()

    def update_last(self, content: str, agent_name: str = None) -> None:
        """Update the last message (for streaming)."""
        if self._turns:
            self._turns[-1].content = content
            if agent_name and self._turns[-1].role == "agent":
                self._turns[-1].agent_name = agent_name
            # Re-render all turns to maintain chat history
            self._render_turns()
    
    def finalize_streaming_message(self, agent_name: str = None) -> None:
        """Finalize the streaming message by adding timestamp."""
        if self._turns and self._turns[-1].role == "agent":
            # Add timestamp to the final message
            from theme import get_palette
            palette = get_palette()
            time_str = self._turns[-1].timestamp.strftime("%H:%M")
            self._turns[-1].content += f"\n{agent_name} ({time_str})"
            self._render_turns()


    def show_welcome(self) -> None:
        """Display the welcome screen."""
        from theme import get_palette
        palette = get_palette()
        
        self._show_welcome = True
        self._turns.clear()
        
        welcome_text = Text()
        welcome_text.append("\n")
        welcome_text.append("                       ███                               ███████     █████████ \n", style=f"{palette.accent}")
        welcome_text.append("                      ░░░                              ███░░░░░███  ███░░░░░███\n", style=f"{palette.accent}")
        welcome_text.append("  ██████   ████████   ████  █████████████    ██████   ███     ░░███░███    ░░░ \n", style=f"{palette.accent}")
        welcome_text.append(" ░░░░░███ ░░███░░███ ░░███ ░░███░░███░░███  ░░░░░███ ░███      ░███░░█████████ \n", style=f"{palette.accent}")
        welcome_text.append("  ███████  ░███ ░███  ░███  ░███ ░███ ░███   ███████ ░███      ░███ ░░░░░░░░███\n", style=f"{palette.accent}")
        welcome_text.append(" ███░░███  ░███ ░███  ░███  ░███ ░███ ░███  ███░░███ ░░███     ███  ███    ░███\n", style=f"{palette.accent}")
        welcome_text.append("░░████████ ████ █████ █████ █████░███ █████░░████████ ░░░███████░  ░░█████████ \n", style=f"{palette.accent}")
        welcome_text.append(" ░░░░░░░░ ░░░░ ░░░░░ ░░░░░ ░░░░░ ░░░ ░░░░░  ░░░░░░░░    ░░░░░░░     ░░░░░░░░░  \n", style=f"{palette.accent}")
        welcome_text.append("\n\n")
        welcome_text.append("                                  animaOS v0.1.0\n", style=f"bold {palette.text_primary}")
        welcome_text.append("                   ────────────────────────────────────────────\n", style=f"{palette.text_secondary}")
        welcome_text.append("                         /help     show help      ctrl+h\n", style=f"{palette.text_secondary}")
        welcome_text.append("                         /agents   list agents    ctrl+a\n", style=f"{palette.text_secondary}")
        welcome_text.append("                         /models   list models    ctrl+m\n", style=f"{palette.text_secondary}")
        welcome_text.append("                         /clear    new session    ctrl+n\n", style=f"{palette.text_secondary}")
        welcome_text.append("                                  /quit     exit\n", style=f"{palette.text_secondary}")
        welcome_text.append("                   ────────────────────────────────────────────\n", style=f"{palette.text_secondary}")
        welcome_text.append("                        Type a message to begin chatting.\n", style=f"{palette.text_secondary}")
        welcome_text.append("\n")
        
        # Check connection status
        if letta_client.test_connection():
            welcome_text.append("                               Connected to Letta.\n", style=f"{palette.success}")
        else:
            welcome_text.append("                            Connection to Letta failed.\n", style=f"{palette.error}")
            
        self._content_widget.update(welcome_text)

    def _render_turns(self) -> None:
        """Render chat messages."""
        from theme import get_palette
        palette = get_palette()
        
        display = Text()
        
        for i, turn in enumerate(self._turns):
            if i > 0:
                display.append("\n\n")
            
            # Get display name for the role
            if turn.role.lower() == "user":
                display_name = os.getenv("DISPLAY_NAME", "User")
            elif turn.role.lower() == "agent":
                # Use actual agent name if available
                display_name = getattr(turn, 'agent_name', None) or "Agent"
            elif turn.role.lower() == "reasoning":
                display_name = "Thinking"
            else:
                display_name = turn.role.title()
            
            # Format timestamp
            time_str = turn.timestamp.strftime("%H:%M")
            
            # Add message content with proper styling
            if turn.role.lower() == "user":
                # User message - with background styling
                lines = turn.content.split('\n')
                for j, line in enumerate(lines):
                    if j > 0:
                        display.append("\n")
                    display.append(f"  {line}  ", style=f"bold {palette.text_primary} on {palette.surface_alt}")
                display.append(f"\n{display_name} ({time_str})", style=f"{palette.text_secondary}")
            else:
                # Agent message
                display.append(f"{turn.content}", style=f"{palette.text_primary}")
                display.append(f"\n{display_name} ({time_str})", style=f"{palette.text_secondary}")
        
        self._content_widget.update(display)


class StatusMessage(Message):
    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__()


class AnimaTUIApp(App):
    """Enhanced TUI that preserves all backend functionality."""
    
    # Static CSS that uses Textual's built-in colors
    CSS = """
    Screen { 
        background: $background; 
        color: $text; 
    }
    #layout { 
        layout: vertical; 
        height: 100%; 
        padding: 1 2; 
    }
    #layout > ChatTranscript { 
        margin-bottom: 1; 
    }
    #transcript { 
        height: 1fr; 
        border: solid $primary; 
        padding: 1; 
        background: $surface;
    }
    #prompt { 
        width: 100%; 
        border: solid $primary; 
        background: $panel; 
        color: $text; 
        padding: 0 1; 
    }
    Footer { 
        background: $panel; 
        color: $text-muted; 
    }
    """
    
    def __init__(self) -> None:
        super().__init__()
        # Use existing backend
        self._agents: List[tuple] = []
        self._current_streaming = False
        self._show_reasoning = False  # Add reasoning support

    def refresh_theme(self) -> None:
        """Refresh the UI after theme change."""
        self.refresh()
        transcript = self.query_one("#transcript", ChatTranscript)
        if transcript._show_welcome:
            transcript.show_welcome()
        else:
            transcript._render_turns()

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+n", "new_session", "New"),
        Binding("ctrl+h", "show_help", "Help"),
        Binding("ctrl+a", "show_agents", "Agents"),
        Binding("ctrl+m", "show_models", "Models"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="layout"):
            transcript = ChatTranscript()
            transcript.id = "transcript"
            yield transcript
            prompt = Input(placeholder="Type your message here...")
            prompt.id = "prompt"
            yield prompt
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app with welcome screen."""
        self.query_one("#transcript", ChatTranscript).show_welcome()
        self._load_agents()
        # Auto-focus the input field for better UX
        self.set_focus(self.query_one("#prompt"))

    def _load_agents(self) -> None:
        """Load agents using existing backend."""
        try:
            agents = letta_client.list_agents()
            if agents:
                self._agents = [(agent["id"], agent["name"]) for agent in agents]
        except Exception as e:
            self._emit_system(f"Error loading agents: {e}")

    def _emit_system(self, message: str) -> None:
        """Add a system message."""
        transcript = self.query_one("#transcript", ChatTranscript)
        transcript.append("system", message)

    def refresh_theme(self) -> None:
        """Refresh the UI after theme change."""
        self._update_css()
        self.refresh()
        transcript = self.query_one("#transcript", ChatTranscript)
        if transcript._show_welcome:
            transcript.show_welcome()
        else:
            transcript._render_turns()

    def watch_dark(self, dark: bool) -> None:
        """Called when dark mode changes."""
        self.refresh_theme()

    def action_new_session(self) -> None:
        """Start a new chat session."""
        transcript = self.query_one("#transcript", ChatTranscript)
        transcript.clear()
        transcript.show_welcome()

    def action_show_help(self) -> None:
        """Show help information using original help text."""
        help_text = """Commands:
  /help     - Show this help
  /status   - Show connection status
  /agents   - List available agents
  /agent <id> - Set agent by ID or number
  /clear    - Clear screen
  /reasoning - Toggle reasoning/thinking display
  /quit     - Exit the application

Note: Use /agent 5 to select agent #5 from the list
Note: Use --reasoning flag to enable reasoning by default"""
        self._emit_system(help_text)

    def action_show_agents(self) -> None:
        """List available agents."""
        if self._agents:
            listing = "\n".join(f"{i+1}. {name} ({agent_id})" for i, (agent_id, name) in enumerate(self._agents))
        else:
            listing = "No agents available. Check connection."
        self._emit_system(f"Available agents:\n{listing}")

    def action_show_models(self) -> None:
        """Show model information."""
        current = letta_client.current_agent_id or "(none)"
        server = config.letta_server_url
        self._emit_system(f"Server: {server}\nCurrent Agent: {current}")

    def action_show_status(self) -> None:
        """Show status information."""
        self.action_show_models()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle message submission using original simple_chat.py logic exactly."""
        message = event.value.strip()
        if not message:
            return

        # Clear input
        event.input.value = ""
        
        # Handle commands
        if message.startswith('/'):
            self.call_after_refresh(self._handle_command, message[1:])
            return

        # Add user message
        transcript = self.query_one("#transcript", ChatTranscript)
        transcript.append("user", message)

        # Start async streaming in background
        self.call_after_refresh(self._stream_response, message)
        
        # Keep focus on input for better UX
        self.set_focus(event.input)

    async def _stream_response(self, message: str) -> None:
        """Handle streaming response exactly like original simple_chat.py."""
        # Get agent name exactly like original
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

        transcript = self.query_one("#transcript", ChatTranscript)
        
        try:
            # Start streaming response
            response = ""
            reasoning_buffer = ""
            
            # Start with agent name prefix like original
            transcript.append("agent", f"[{agent_name}] ", agent_name)
            
            async for chunk in letta_client.send_message_stream(message, show_reasoning=self._show_reasoning):
                if chunk.startswith("__REASONING__:"):
                    # This is reasoning content - buffer it
                    reasoning_content = chunk[14:]  # Remove "__REASONING__:" prefix
                    reasoning_buffer += reasoning_content
                else:
                    # This is regular content
                    # If we have buffered reasoning, display it first
                    if reasoning_buffer:
                        transcript.append("reasoning", f"[Thinking] {reasoning_buffer}")
                        response += f"[Thinking] {reasoning_buffer}"
                        reasoning_buffer = ""
                    
                    # Stream the chunk exactly as received from API
                    transcript.update_last(f"[{agent_name}] {response}{chunk}", agent_name)
                    response += chunk
                    
                    # Allow UI to refresh after each chunk
                    await asyncio.sleep(0.01)
            
            # Handle any remaining reasoning buffer
            if reasoning_buffer:
                transcript.append("reasoning", f"[Thinking] {reasoning_buffer}")

        except Exception as e:
            # Show actual error message like original
            transcript.append("agent", f"Error: {e}", agent_name)

    async def _handle_command(self, command: str) -> None:
        """Handle chat commands using original simple_chat.py logic exactly."""
        parts = command.split()
        cmd = parts[0].lower()
        
        if cmd == "help":
            self.action_show_help()
        elif cmd == "status":
            self.action_show_status()
        elif cmd == "agents":
            await self._list_agents()
        elif cmd == "agent":
            if len(parts) > 1:
                await self._set_agent(parts[1])
            else:
                self._emit_system("Usage: /agent <id or number>")
        elif cmd == "clear":
            self.action_new_session()
        elif cmd == "reasoning":
            self._show_reasoning = not self._show_reasoning
            status = "enabled" if self._show_reasoning else "disabled"
            self._emit_system(f"Reasoning display {status}")
        elif cmd == "quit":
            self.exit()
        else:
            self._emit_system(f"Unknown command: /{cmd}. Type /help for available commands.")

    async def _list_agents(self) -> None:
        """List available agents using original logic."""
        self._emit_system("Fetching available agents...")
        agents = letta_client.list_agents()
        if agents:
            listing = f"Found {len(agents)} agents:\n"
            for i, agent in enumerate(agents, 1):
                listing += f"  {i}. {agent['name']} (ID: {agent['id']})\n"
                if agent.get('description'):
                    listing += f"      {agent['description']}\n"
            self._emit_system(listing)
        else:
            self._emit_system("No agents found or error occurred")

    async def _set_agent(self, agent_id: str) -> None:
        """Set the active agent by ID or number using original logic."""
        # Check if it's a number (from the list)
        if agent_id.isdigit():
            agents = letta_client.list_agents()
            try:
                agent_index = int(agent_id) - 1  # Convert to 0-based index
                if 0 <= agent_index < len(agents):
                    actual_agent_id = agents[agent_index]['id']
                    if letta_client.set_agent(actual_agent_id):
                        self._emit_system(f"Set agent: {agents[agent_index]['name']} (ID: {actual_agent_id})")
                    else:
                        self._emit_system(f"Failed to set agent: {agent_id}")
                else:
                    self._emit_system(f"Invalid agent number: {agent_id}. Use /agents to see available agents.")
            except (ValueError, IndexError):
                self._emit_system(f"Invalid agent number: {agent_id}. Use /agents to see available agents.")
        else:
            # Try as direct agent ID
            if letta_client.set_agent(agent_id):
                self._emit_system(f"Set agent: {agent_id}")
            else:
                self._emit_system(f"Failed to set agent: {agent_id}")


def run(reasoning=False):
    """Launch the enhanced TUI app."""
    app = AnimaTUIApp()
    app._show_reasoning = reasoning  # Set reasoning flag
    app.run()


if __name__ == "__main__":
    run()