#!/usr/bin/env python3
"""
Enhanced TUI Chat Interface
Maps beautiful UI to existing animus-chat functionality

Copyright (C) 2024 AnimusUNO
"""
import os
import sys
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Static, Input, Footer
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

    def append(self, role: str, content: str) -> None:
        """Add a new message turn."""
        self._turns.append(ChatTurn(role=role, content=content, timestamp=datetime.now()))
        self._show_welcome = False
        self._render_turns()
        # Auto-scroll to bottom
        self.scroll_end()

    def update_last(self, content: str) -> None:
        """Update the last message (for streaming)."""
        if self._turns:
            self._turns[-1].content = content
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
        welcome_text.append("                         /new      new session    ctrl+n\n", style=f"{palette.text_secondary}")
        welcome_text.append("                         /help     show help      ctrl+h\n", style=f"{palette.text_secondary}")
        welcome_text.append("                         /agents   list agents    ctrl+a\n", style=f"{palette.text_secondary}")
        welcome_text.append("                         /models   list models    ctrl+m\n", style=f"{palette.text_secondary}")
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
            else:
                display_name = "Agent"
            
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
        """Show help information."""
        self._emit_system("Commands: /help /status /agents /agent <id> /clear /quit")

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

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle message submission using existing backend."""
        message = event.value.strip()
        if not message:
            return

        # Clear input
        event.input.value = ""
        
        # Handle commands
        if message.startswith('/'):
            self._handle_command(message[1:])
            return

        # Add user message
        transcript = self.query_one("#transcript", ChatTranscript)
        transcript.append("user", message)

        # Send to agent using existing backend
        try:
            # Get response from Letta (synchronous)
            response_content = letta_client.send_message(message)
            if response_content:
                transcript.append("agent", response_content)
            else:
                transcript.append("system", "No response from agent")
            
        except Exception as e:
            transcript.append("system", f"Error: {e}")

    def _handle_command(self, command: str) -> None:
        """Handle chat commands using existing backend functionality."""
        parts = command.split()
        cmd = parts[0].lower()
        
        if cmd == "help":
            self.action_show_help()
        elif cmd == "status":
            self.action_show_models()
        elif cmd == "agents":
            self.action_show_agents()
        elif cmd == "agent" and len(parts) > 1:
            # Set agent using existing backend
            try:
                agent_id = parts[1]
                letta_client.set_agent(agent_id)
                self._emit_system(f"Agent set to: {agent_id}")
            except Exception as e:
                self._emit_system(f"Error setting agent: {e}")
        elif cmd == "clear":
            self.action_new_session()
        elif cmd == "quit":
            self.exit()
        else:
            self._emit_system(f"Unknown command: /{command}")


def run():
    """Launch the enhanced TUI app."""
    app = AnimaTUIApp()
    app.run()


if __name__ == "__main__":
    run()