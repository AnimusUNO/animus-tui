"""Textual scaffolding and chat logic for animaOS."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List, Tuple
from datetime import datetime
import os

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Center, Middle
from textual.events import Mount
from textual.message import Message
from textual.widgets import Footer, Input, Static

from rich.text import Text

# Knowledge functionality removed for animus-chat compatibility
from animaos.theme import palette
from config import config
from letta_api import letta_client


ASCII_LOGO = r"""
                       ███                               ███████     █████████ 
                      ░░░                              ███░░░░░███  ███░░░░░███
  ██████   ████████   ████  █████████████    ██████   ███     ░░███░███    ░░░ 
 ░░░░░███ ░░███░░███ ░░███ ░░███░░███░░███  ░░░░░███ ░███      ░███░░█████████ 
  ███████  ░███ ░███  ░███  ░███ ░███ ░███   ███████ ░███      ░███ ░░░░░░░░███
 ███░░███  ░███ ░███  ░███  ░███ ░███ ░███  ███░░███ ░░███     ███  ███    ░███
░░████████ ████ █████ █████ █████░███ █████░░████████ ░░░███████░  ░░█████████ 
 ░░░░░░░░ ░░░░ ░░░░░ ░░░░░ ░░░░░ ░░░ ░░░░░  ░░░░░░░░    ░░░░░░░     ░░░░░░░░░  
                                                                                
                                                                                
                                                                                
"""


@dataclass
class ChatTurn:
    role: str
    content: str
    timestamp: datetime


class ChatTranscript(Static):
    """Transcript widget with ASCII framing."""

    DEFAULT_CSS = """ChatTranscript {width: 100%;}"""

    def __init__(self) -> None:
        super().__init__(id="transcript")
        self._turns: List[ChatTurn] = []
        self._display: Text = Text("")
        self._is_initial = True

    def clear(self) -> None:
        self._turns.clear()
        self._display = Text("")
        self._is_initial = True
        self.refresh(layout=True)

    def append(self, role: str, content: str) -> None:
        self._turns.append(ChatTurn(role=role, content=content, timestamp=datetime.now()))
        self._is_initial = False
        self._render_turns()

    def update_last(self, content: str) -> None:
        if self._turns:
            self._turns[-1].content = content
            self._render_turns()

    def set_text(self, text: str) -> None:
        """Replace the display with raw text (used for home screen)."""

        self._turns.clear()
        self._display = Text.from_markup(text)
        self.refresh(layout=True)

    def _render_turns(self) -> None:
        display = Text()
        
        for i, turn in enumerate(self._turns):
            if i > 0:
                display.append("\n\n")
            
            # Get display name for the role
            if turn.role.lower() == "you":
                display_name = os.getenv("DISPLAY_NAME", "User")
            elif turn.role.lower() == "agent":
                display_name = "Claude Opus 4.1"  # Default agent name, could be configured
            else:
                display_name = turn.role.title()
            
            # Format timestamp
            time_str = turn.timestamp.strftime("%H:%M")
            
            # Add message content with proper styling
            if turn.role.lower() == "you":
                # User message with background - right aligned
                padded_content = f" {turn.content} "
                padded_meta = f" {display_name} ({time_str}) "
                display.append(f"{padded_content:>70}", style=f"bold {palette.text_primary} on {palette.surface}")
                display.append(f"\n{padded_meta:>70}", style=f"{palette.text_secondary} on {palette.surface_alt}")
            elif turn.role.lower() == "agent":
                # Agent message with background - left aligned  
                padded_content = f" {turn.content} "
                padded_meta = f" {display_name} ({time_str}) "
                display.append(padded_content, style=f"{palette.text_primary} on {palette.surface}")
                display.append(f"\n{padded_meta}", style=f"{palette.text_secondary} on {palette.surface_alt}")
            else:
                # System message
                display.append(f"{turn.content}", style=f"italic {palette.text_secondary}")
                display.append(f"\n{display_name} ({time_str})", style=f"dim {palette.text_secondary}")
        
        self._display = display
        self.refresh(layout=True)

    def render(self) -> Text:
        if self._is_initial and not self._turns:
            # Center the initial content by adding padding
            lines = str(self._display).split('\n')
            centered_text = Text()
            terminal_width = 160  # Assume reasonable terminal width
            
            for line in lines:
                if line.strip():
                    # Calculate padding to center the line
                    padding = max(0, (terminal_width - len(line.strip())) // 2)
                    centered_line = " " * padding + line.strip()
                    centered_text.append(centered_line + "\n")
                else:
                    centered_text.append("\n")
            return centered_text
        else:
            # Normal chat mode - no centering
            return self._display


class StatusMessage(Message):
    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__()


class AnimaOSApp(App[None]):
    """Textual application with chat logic."""

    CSS = f"""
    Screen {{ background: {palette.background}; color: {palette.text_primary}; }}
    #layout {{ layout: vertical; height: 100%; padding: 1 2; }}
    #layout > ChatTranscript {{ margin-bottom: 1; }}
    #transcript {{ height: 1fr; border: solid {palette.border}; padding: 1; }}
    #prompt {{ width: 100%; border: solid {palette.border}; background: {palette.surface}; color: {palette.text_primary}; padding: 0 1; }}
    Footer {{ background: {palette.surface_alt}; color: {palette.text_secondary}; }}
    .user-message {{ 
        background: {palette.surface}; 
        border: solid {palette.border}; 
        padding: 1; 
        margin: 1 0; 
        text-align: right;
    }}
    .agent-message {{ 
        background: {palette.background}; 
        border: solid {palette.border}; 
        padding: 1; 
        margin: 1 0; 
        text-align: left;
    }}
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+n", "new_session", "New"),
        Binding("ctrl+h", "show_help", "Help"),
        Binding("ctrl+a", "show_agents", "Agents"),
        Binding("ctrl+m", "show_models", "Models"),
        # Knowledge keybinding removed
    ]

    def __init__(self) -> None:
        super().__init__()
        self._transcript = ChatTranscript()
        self._in_chat = False
        self._prompt: Input | None = None
        # Knowledge functionality removed for animus-chat compatibility
        self._agents: List[Tuple[str, str]] = []
        self._home_messages: List[str] = []

    async def on_mount(self, event: Mount) -> None:
        self._show_home()
        await self._initialize()

    async def _initialize(self) -> None:
        if not config.validate():
            self._emit_system("Config invalid: run config.py")
            return

        loop = asyncio.get_running_loop()

        # Run blocking API calls off the main loop
        connected = await loop.run_in_executor(None, letta_client.test_connection)
        if connected:
            self._emit_system("Connected to Letta.")
            agents = await loop.run_in_executor(None, letta_client.list_agents)
            self._agents = [(agent["id"], agent["name"]) for agent in agents]
            if not self._agents:
                self._emit_system("No agents returned from server.")
        else:
            self._emit_system("Letta connection failed.")

    def compose(self) -> ComposeResult:  # pragma: no cover - layout only
        self._prompt = Input(placeholder="> ", id="prompt")
        yield Container(self._transcript, self._prompt, id="layout")
        yield Footer()

    def _focus_prompt(self) -> None:
        if self._prompt is not None:
            self.set_focus(self._prompt)

    def _show_home(self) -> None:
        self._in_chat = False
        # Knowledge functionality removed
        self._home_messages.clear()
        self._transcript.set_text(self._home_screen_text())
        if self._prompt is not None:
            self._prompt.placeholder = "> "
            self._prompt.value = ""
        self.call_after_refresh(self._focus_prompt)

    def _enter_chat(self) -> None:
        if not self._in_chat:
            self._in_chat = True
            self._transcript.clear()
            self._emit_system("Session started. Type /help for commands.")
            if self._prompt is not None:
                self._prompt.placeholder = "> "
                self._prompt.value = ""
            self.call_after_refresh(self._focus_prompt)

    def _home_screen_text(self) -> str:
        commands = (
            "/new      new session    ctrl+n\n"
            "/help     show help      ctrl+h\n"
            "/agents   list agents    ctrl+a\n"
            "/models   list models    ctrl+m\n"
            "\n"
            "/quit     exit"
        )
        extra = "\n\n".join(self._home_messages)
        body = (
            f"{ASCII_LOGO}\n\n"
            "animaOS v0.1.0\n"
            "────────────────────────────────────────────\n"
            f"{commands}\n"
            "────────────────────────────────────────────\n"
            "Type a message to begin chatting."
        )
        if extra:
            body = f"{body}\n\n{extra}"
        return body

    def _refresh_home(self) -> None:
        if not self._in_chat:
            self._transcript.set_text(self._home_screen_text())

    def action_new_session(self) -> None:
        self._show_home()

    async def handle_input(self, value: str) -> None:
        text = value.strip()
        if not text:
            return

        if text.startswith("/"):
            await self._handle_command(text[1:])
            return

        self._enter_chat()
        self._transcript.append("you", text)
        await self._respond(text)

    async def _handle_command(self, command_line: str) -> None:
        parts = command_line.split(" ", 1)
        command = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if command == "help":
            self._emit_system("Commands: /help /status /agents /agent <id> /clear /quit")
        elif command == "status":
            agent = letta_client.current_agent_id or "(none)"
            self._emit_system(f"Server: {config.letta_server_url}\nAgent: {agent}")
        elif command == "agents":
            if self._agents:
                listing = "\n".join(f"{i+1}. {name} ({agent_id})" for i, (agent_id, name) in enumerate(self._agents))
            else:
                listing = "No agents cached."
            self._emit_system(listing)
        elif command == "agent":
            if not arg:
                self._emit_system("Usage: /agent <id or number>")
                return
            await self._set_agent(arg)
        elif command == "new":
            self.action_new_session()
        elif command == "clear":
            if self._in_chat:
                self._transcript.clear()
            else:
                self._home_messages.clear()
                self._refresh_home()
        # Knowledge command removed for animus-chat compatibility
        elif command == "quit":
            self.exit()
        else:
            self._emit_system(f"Unknown command: {command}")

    async def _set_agent(self, arg: str) -> None:
        loop = asyncio.get_running_loop()
        agent_id = arg
        if arg.isdigit() and self._agents:
            idx = int(arg) - 1
            if 0 <= idx < len(self._agents):
                agent_id = self._agents[idx][0]
        success = await loop.run_in_executor(None, letta_client.set_agent, agent_id)
        if success:
            self._emit_system(f"Agent set to {agent_id}.")
        else:
            self._emit_system(f"Failed to set agent {agent_id}.")

    async def _respond(self, text: str) -> None:
        # Knowledge functionality removed for animus-chat compatibility

        loop = asyncio.get_running_loop()
        current_agent = getattr(letta_client, "current_agent_id", None)
        if not current_agent:
            self._emit_system("No agent selected. Use /agents then /agent <id> to choose one.")
            return

        try:
            stream = letta_client.send_message_stream(text, show_reasoning=False)
        except Exception as error:  # pragma: no cover - defensive path
            self._emit_system(f"Failed to contact agent: {error}")
            return

        if stream is None:
            self._emit_system("Agent stream unavailable. Verify connection and agent selection.")
            return

        self._transcript.append("agent", "")

        try:
            async for chunk in stream:
                current_text = chunk.replace("\\n", "\n") if isinstance(chunk, str) else str(chunk)
                current = (self._transcript._turns[-1].content if self._transcript._turns else "") + current_text
                self._transcript.update_last(current)
                await asyncio.sleep(0)
        except TypeError:
            self._transcript.update_last("Error: agent did not provide a stream response.")
        except Exception as error:  # pragma: no cover - API errors
            self._transcript.update_last(f"Error: {error}")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if self._prompt is not None and event.input.id == "prompt":
            await self.handle_input(event.value)
            event.input.value = ""

    async def on_status_message(self, message: StatusMessage) -> None:
        self._emit_system(message.text)

    # Knowledge action removed for animus-chat compatibility

    def action_show_help(self) -> None:
        self._emit_system(
            "Keyboard: ctrl+n new, ctrl+h help, ctrl+a agents, ctrl+m models, ctrl+q quit"
        )

    def action_show_agents(self) -> None:
        if self._agents:
            listing = "\n".join(f"{i+1}. {name} ({agent_id})" for i, (agent_id, name) in enumerate(self._agents))
        else:
            listing = "No agents cached."
        self._emit_system(listing)

    def action_show_models(self) -> None:
        self._emit_system("Model listing not yet implemented.")

    def _emit_system(self, text: str) -> None:
        if self._in_chat:
            self._transcript.append("system", text)
        else:
            self._home_messages.append(text)
            self._refresh_home()


def run() -> None:
    AnimaOSApp().run()

