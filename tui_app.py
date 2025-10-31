#!/usr/bin/env python3
"""
Enhanced TUI Chat Interface
Maps beautiful UI to existing animus-chat functionality

Copyright (C) 2024 AnimusUNO
"""
import asyncio
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
from rich.markdown import Markdown
import re

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


def parse_markdown_to_rich(text: str, base_style: str = "") -> Text:
    """Parse markdown formatting and convert to Rich Text object."""
    from theme import get_palette
    palette = get_palette()
    
    # Replace literal \n with actual newlines (LLMs sometimes output this)
    text = text.replace('\\n', '\n')
    
    result = Text()
    
    # Split by lines to handle formatting line by line
    lines = text.split('\n')
    
    for line_idx, line in enumerate(lines):
        if line_idx > 0:
            result.append('\n')
        
        # Handle list items
        list_match = re.match(r'^(\s*)([-*]|\d+\.)\s+(.*)$', line)
        if list_match:
            indent = list_match.group(1)
            marker = list_match.group(2)
            content = list_match.group(3)
            result.append(indent)
            result.append(f"{marker} ", style=f"{palette.accent}")
            # Parse the rest of the line for formatting
            line = content
        
        # Handle headers
        header_match = re.match(r'^(#{1,6})\s+(.*)$', line)
        if header_match:
            level = len(header_match.group(1))
            content = header_match.group(2)
            # Render headers as bold with accent color
            result.append(content, style=f"bold {palette.accent}")
            continue
        
        # Parse inline markdown patterns
        # Pattern priority: links, bold, italic, code
        patterns = [
            (r'\[([^\]]+)\]\(([^)]+)\)', 'link'),  # [text](url)
            (r'\*\*([^*]+)\*\*', 'bold'),           # **bold**
            (r'__([^_]+)__', 'bold'),               # __bold__
            (r'\*([^*]+)\*', 'italic'),             # *italic*
            (r'_([^_]+)_', 'italic'),               # _italic_
            (r'`([^`]+)`', 'code'),                 # `code`
        ]
        
        # Find all matches
        matches = []
        for pattern, match_type in patterns:
            for match in re.finditer(pattern, line):
                matches.append((match.start(), match.end(), match, match_type))
        
        # Sort by position
        matches.sort(key=lambda x: x[0])
        
        # Remove overlapping matches (keep first)
        filtered = []
        last_end = 0
        for start, end, match, match_type in matches:
            if start >= last_end:
                filtered.append((start, end, match, match_type))
                last_end = end
        
        # Build the rich text
        last_pos = 0
        for start, end, match, match_type in filtered:
            # Add text before match
            if start > last_pos:
                result.append(line[last_pos:start], style=base_style)
            
            # Add formatted text
            if match_type == 'link':
                text_part = match.group(1)
                url = match.group(2)
                # Show link text with URL in parentheses (clickable not possible in TUI)
                result.append(text_part, style=f"bold {palette.accent} underline")
                result.append(f" ({url})", style=f"{palette.text_secondary}")
            elif match_type == 'bold':
                result.append(match.group(1), style=f"bold {base_style}")
            elif match_type == 'italic':
                result.append(match.group(1), style=f"italic {base_style}")
            elif match_type == 'code':
                result.append(f" {match.group(1)} ", style=f"{palette.warning} on {palette.surface_alt}")
            
            last_pos = end
        
        # Add remaining text
        if last_pos < len(line):
            result.append(line[last_pos:], style=base_style)
    
    return result


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

    def update_last(self, content: str) -> None:
        """Update the last message (for streaming)."""
        if self._turns:
            self._turns[-1].content = content
            self._render_turns()
    
    def remove_last(self) -> None:
        """Remove the last message."""
        if self._turns:
            self._turns.pop()
            self._render_turns()

    def show_welcome(self) -> None:
        """Display the welcome screen."""
        from theme import get_palette
        palette = get_palette()
        
        self._show_welcome = True
        self._turns.clear()
        
        # Determine ASCII art color based on theme mode
        from theme import _dark_mode, _current_theme
        # Use white for dark themes, black for light themes
        ascii_color = "white" if _dark_mode else "black"
        
        welcome_text = Text()
        welcome_text.append("\n")
        welcome_text.append("                       ███                               ███████     █████████ \n", style=ascii_color)
        welcome_text.append("                      ░░░                              ███░░░░░███  ███░░░░░███\n", style=ascii_color)
        welcome_text.append("  ██████   ████████   ████  █████████████    ██████   ███     ░░███░███    ░░░ \n", style=ascii_color)
        welcome_text.append(" ░░░░░███ ░░███░░███ ░░███ ░░███░░███░░███  ░░░░░███ ░███      ░███░░█████████ \n", style=ascii_color)
        welcome_text.append("  ███████  ░███ ░███  ░███  ░███ ░███ ░███   ███████ ░███      ░███ ░░░░░░░░███\n", style=ascii_color)
        welcome_text.append(" ███░░███  ░███ ░███  ░███  ░███ ░███ ░███  ███░░███ ░░███     ███  ███    ░███\n", style=ascii_color)
        welcome_text.append("░░████████ ████ █████ █████ █████░███ █████░░████████ ░░░███████░  ░░█████████ \n", style=ascii_color)
        welcome_text.append(" ░░░░░░░░ ░░░░ ░░░░░ ░░░░░ ░░░░░ ░░░ ░░░░░  ░░░░░░░░    ░░░░░░░     ░░░░░░░░░  \n", style=ascii_color)
        welcome_text.append("\n\n")
        welcome_text.append("                                  animaOS v0.1.0\n", style=f"bold {palette.text_primary}")
        welcome_text.append("                   ────────────────────────────────────────────\n", style=f"{palette.text_secondary}")
        welcome_text.append("                         /new      new session    ctrl+n\n", style=f"{palette.text_secondary}")
        welcome_text.append("                         /help     show help      ctrl+h\n", style=f"{palette.text_secondary}")
        welcome_text.append("                         /agents   list agents    ctrl+a\n", style=f"{palette.text_secondary}")
        welcome_text.append("                         /status   show status    ctrl+s\n", style=f"{palette.text_secondary}")
        welcome_text.append("                         /text     text palettes\n", style=f"{palette.text_secondary}")
        welcome_text.append("                                  /quit     exit\n", style=f"{palette.text_secondary}")
        welcome_text.append("                   ────────────────────────────────────────────\n", style=f"{palette.text_secondary}")
        welcome_text.append("                        Type a message to begin chatting.\n", style=f"{palette.text_secondary}")
        welcome_text.append("\n")
        
        # Check connection status
        if letta_client.test_connection():
            welcome_text.append("                        Connected to Animus (Letta Instance)\n", style=f"{palette.success}")
        else:
            welcome_text.append("                      Connection to Animus (Letta Instance) failed.\n", style=f"{palette.error}")
            
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
            elif turn.role.lower() == "reasoning":
                # Reasoning block - styled prominently like Letta interface (purple/lavender)
                # Use accent color with italic styling for reasoning
                reasoning_lines = turn.content.split('\n')
                for j, line in enumerate(reasoning_lines):
                    if j > 0:
                        display.append("\n")
                    # Purple/lavender color for reasoning (using accent or a custom purple)
                    display.append(f"  {line}  ", style=f"italic {palette.accent}")
                display.append(f"\n{display_name} ({time_str})", style=f"dim {palette.text_secondary}")
            else:
                # Agent message - parse markdown formatting
                formatted_content = parse_markdown_to_rich(turn.content, palette.text_primary)
                display.append(formatted_content)
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
        border: solid grey; 
        padding: 1; 
        background: $surface;
    }
    #prompt { 
        width: 100%; 
        border: solid grey; 
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
        self._loading_task = None  # Background task for loading animation
        
        # Load saved theme preference
        self._load_theme_preference()

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
        Binding("ctrl+s", "show_status", "Status"),
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
        # Load theme preference must happen before setting dark mode
        # (already called in __init__, but we refresh here to apply it)
        self.refresh_theme()
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

    def watch_dark(self, dark: bool) -> None:
        """Called when dark mode changes."""
        from theme import set_dark_mode
        set_dark_mode(dark)
        self._save_theme_preference()
        self.refresh_theme()
    
    def watch_theme(self, theme: str) -> None:
        """Called when theme changes."""
        self._save_theme_preference()
    
    def _load_theme_preference(self) -> None:
        """Load saved theme preference from config file."""
        import json
        from theme import set_theme, set_dark_mode
        config_file = Path(__file__).parent / ".tui_config.json"
        try:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    # Load custom theme name if available
                    if 'custom_theme' in config:
                        set_theme(config['custom_theme'])
                    # Load Textual theme if available
                    if 'theme' in config:
                        self.theme = config['theme']
                    # Load dark mode
                    if 'dark_mode' in config:
                        self.dark = config['dark_mode']
                        set_dark_mode(config['dark_mode'])
        except Exception:
            # If loading fails, use defaults
            pass
    
    def _save_theme_preference(self) -> None:
        """Save theme preference to config file."""
        import json
        from theme import _current_theme
        config_file = Path(__file__).parent / ".tui_config.json"
        try:
            config = {}
            # Load existing config if it exists
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
            # Save current theme info
            config['custom_theme'] = _current_theme
            config['theme'] = self.theme
            config['dark_mode'] = self.dark
            # Save back
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            # Silently fail - not critical
            pass

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
  /text     - List available text color palettes
  /text <name> - Set text palette (e.g., /text nord)
  /clear    - Clear screen
  /reasoning - Toggle reasoning/thinking display
  /vibe     - Enter vibe mode 
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
    
    async def _animate_loading(self) -> None:
        """Animate the loading indicator with a rotating spinner (inspired by Gum)."""
        transcript = self.query_one("#transcript", ChatTranscript)
        # Unicode spinner frames (dots style - smooth and modern)
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        idx = 0
        while self._current_streaming:
            transcript.update_last(f"{frames[idx]} Thinking...")
            idx = (idx + 1) % len(frames)
            await asyncio.sleep(0.08)  # Fast animation (80ms per frame)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle message submission using original simple_chat.py logic exactly."""
        message = event.value.strip()
        if not message:
            return

        # Clear input immediately for instant feedback
        event.input.value = ""
        
        # Handle commands
        if message.startswith('/'):
            await self._handle_command(message[1:])
            return

        # Add user message
        transcript = self.query_one("#transcript", ChatTranscript)
        transcript.append("user", message)
        
        # Send message to agent
        await self._send_message_to_agent(message)

    async def _send_message_to_agent(self, message: str) -> None:
        """Helper method to send a message to the agent and handle streaming response."""
        transcript = self.query_one("#transcript", ChatTranscript)
        
        # Get agent name and model info FIRST (quick)
        agent_name = "Assistant"  # Default fallback
        model_name = "Model"
        if letta_client and letta_client.current_agent_id:
            try:
                agents = letta_client.list_agents()
                if agents and isinstance(agents, list):
                    for agent in agents:
                        if isinstance(agent, dict) and 'id' in agent and 'name' in agent:
                            if agent['id'] == letta_client.current_agent_id:
                                agent_name = agent['name']
                                # Try multiple paths to get model name
                                if 'llm_config' in agent:
                                    llm_config = agent['llm_config']
                                    if isinstance(llm_config, dict):
                                        model_name = llm_config.get('model', llm_config.get('model_name', 'Model'))
                                    elif isinstance(llm_config, str):
                                        model_name = llm_config
                                elif 'model' in agent:
                                    model_name = agent['model']
                                # Clean up model name (remove provider prefix if present)
                                if isinstance(model_name, str) and '/' in model_name:
                                    model_name = model_name.split('/')[-1]
                                break
            except Exception as e:
                # If we can't get the agent info, fall back to defaults
                pass
        
        # Add loading indicator with model name
        transcript.append("agent", "⠋ Thinking...", model_name)
        transcript.scroll_end()
        
        # Start loading animation
        self._current_streaming = True
        loading_task = asyncio.create_task(self._animate_loading())
        
        # Yield to event loop to let animation start
        await asyncio.sleep(0)

        try:
            # Stream reasoning and answer incrementally
            first_chunk = True
            agent_started = False
            
            async for chunk in letta_client.send_message_stream(message, show_reasoning=self._show_reasoning):
                # Normalize content
                current_text = chunk

                # Handle reasoning chunks emitted by letta_api with special marker
                if isinstance(current_text, str) and current_text.startswith("__REASONING__:"):
                    reasoning_content = current_text[14:]
                    if first_chunk:
                        # Replace spinner with reasoning immediately
                        self._current_streaming = False
                        await loading_task
                        transcript.remove_last()
                        first_chunk = False
                    # Append or update a reasoning turn as it streams
                    if transcript._turns and transcript._turns[-1].role == "reasoning":
                        transcript.update_last(transcript._turns[-1].content + reasoning_content)
                    else:
                        transcript.append("reasoning", reasoning_content)
                    continue

                # Regular content (agent answer)
                if first_chunk:
                    self._current_streaming = False
                    await loading_task
                    transcript.remove_last()
                    first_chunk = False

                if not agent_started:
                    # Start an agent turn we can update incrementally
                    transcript.append("agent", "", agent_name)
                    agent_started = True

                processed_content = current_text.replace("\\n", "\n") if isinstance(current_text, str) else str(current_text)
                current = (transcript._turns[-1].content if transcript._turns else "") + processed_content
                transcript.update_last(current)

        except Exception as e:
            # Stop loading animation
            self._current_streaming = False
            if loading_task and not loading_task.done():
                await loading_task
            # Remove loading indicator if still present
            if first_chunk:
                transcript.remove_last()
            # Show actual error message like original
            transcript.append("agent", f"Error: {e}", agent_name)

    async def _handle_command(self, command: str) -> None:
        """Handle chat commands using original simple_chat.py logic exactly."""
        parts = command.split()
        cmd = parts[0].lower()
        arg = parts[1].lower() if len(parts) > 1 else ""
        
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
        elif cmd == "text":
            if len(parts) > 1:
                self._set_text_palette(parts[1])
            else:
                self._list_text_palettes()
        elif cmd == "clear":
            self.action_new_session()
        elif cmd == "reasoning":
            self._show_reasoning = not self._show_reasoning
            status = "enabled" if self._show_reasoning else "disabled"
            self._emit_system(f"Reasoning display {status}")
        elif cmd == "vibe":
            # Subcommands: start (default), stop, status
            if arg == "stop":
                self._vibe_write_command("stop")
                self._emit_system("Vibe mode stopping…")
                return
            if arg == "status":
                state = self._vibe_read_state()
                if state:
                    msg = f"Vibe status: {state.get('status','unknown')} pid={state.get('pid','?')} last_run={state.get('last_run','-')}"
                else:
                    msg = "Vibe status: not running"
                self._emit_system(msg)
                return

            # Default: start
            started = self._vibe_start_process_if_needed()
            if started:
                self._emit_system("Entering vibe mode (autonomous)")
                self._vibe_write_command("start")
            else:
                self._emit_system("Vibe mode already running")
            # Also send the immediate run prompt once
            await self._send_message_to_agent(config.vibe_mode_prompt)
        elif cmd == "quit":
            self.exit()
        else:
            self._emit_system(f"Unknown command: /{cmd}. Type /help for available commands.")
    
    def _list_text_palettes(self) -> None:
        """List available text color palettes."""
        from theme import get_available_themes, _current_theme
        palettes = get_available_themes()
        listing = "Available text palettes:\n"
        for palette in palettes:
            marker = "→ " if palette == _current_theme else "  "
            listing += f"{marker}{palette}\n"
        listing += "\nUsage: /text <name>"
        self._emit_system(listing)
    
    def _set_text_palette(self, palette_name: str) -> None:
        """Set the active text color palette."""
        from theme import set_theme, get_available_themes
        palettes = get_available_themes()
        if palette_name in palettes:
            set_theme(palette_name)
            self._save_theme_preference()
            self.refresh_theme()
            self._emit_system(f"Text palette set to: {palette_name}")
        else:
            self._emit_system(f"Unknown palette: {palette_name}\nAvailable palettes: {', '.join(palettes)}")

    # ----- Vibe process helpers -----
    def _vibe_control_path(self):
        from pathlib import Path
        return Path(config.vibe_control_file)

    def _vibe_read_state(self):
        import json
        try:
            path = self._vibe_control_path()
            if not path.exists():
                return {}
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _vibe_write_command(self, command: str):
        import json
        state = self._vibe_read_state()
        state.update({
            "last_command": command,
        })
        try:
            self._vibe_control_path().write_text(json.dumps(state, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _vibe_process_running(self, pid: int) -> bool:
        if not pid:
            return False
        try:
            # Cross-platform best-effort check
            os.kill(pid, 0)  # type: ignore[attr-defined]
            return True
        except Exception:
            return False

    def _vibe_start_process_if_needed(self) -> bool:
        state = self._vibe_read_state()
        pid = state.get("pid")
        if pid and self._vibe_process_running(pid):
            return False

        # Launch background process
        try:
            import subprocess, sys
            script_path = str((Path(__file__).parent / "vibe_mode.py"))
            # Use the same Python interpreter
            subprocess.Popen([sys.executable, script_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=str(Path(__file__).parent))
            return True
        except Exception as e:
            self._emit_system(f"Failed to start vibe mode: {e}")
            return False

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