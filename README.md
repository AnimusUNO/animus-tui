# Letta Chat Client

A simple, clean text-based chat client for Letta AI agents.

## Features

- Simple text interface - no complex UI
- Real-time message streaming
- Agent selection and management
- Configuration stored in `.env` file
- Idempotent - can be run multiple times safely

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Run the interactive setup to configure your environment:

```bash
python config.py
```

This will:
- Ask for your Letta server URL
- Ask for your API token
- Test the connection to verify credentials
- Fetch available agents and let you select a default
- Save everything to `.env` file

Alternatively, you can manually copy and edit the environment file:

```bash
copy env.example .env
```

Edit `.env` with your Letta server details:

```env
LETTA_SERVER_URL=https://your-letta-server.com:8283
LETTA_API_TOKEN=your_api_token_here
DISPLAY_NAME=YourName
DEFAULT_AGENT_ID=your_agent_id_here
```

### 3. Run the Client

```bash
python main.py
```

## Usage

### Commands

- `/help` - Show help
- `/status` - Show connection status
- `/agents` - List available agents
- `/agent <id>` - Set agent by ID
- `/clear` - Clear screen
- `/quit` - Exit

### Chat

Just type your message and press Enter to send it to the selected agent.

## File Structure

```
TUI-chat/
├── docs/
│   ├── PROJECT_PLAN.md
│   └── letta-api-reference.md
├── simple_chat.py      # Main chat interface
├── config.py          # Configuration management
├── letta_client.py    # Letta API wrapper
├── main.py            # Entry point
├── requirements.txt   # Dependencies
├── env.example       # Environment template
└── README.md         # This file
```

## Configuration

All configuration is stored in the `.env` file:

- `LETTA_SERVER_URL` - Your Letta server URL
- `LETTA_API_TOKEN` - Your API token
- `DISPLAY_NAME` - Your display name in chat
- `DEFAULT_AGENT_ID` - Agent to use by default

## Troubleshooting

1. **Connection failed**: Check your `LETTA_SERVER_URL` and `LETTA_API_TOKEN`
2. **No agents found**: Verify your API token has access to agents
3. **Agent not responding**: Check the agent ID is correct

## Development

This is a minimal implementation focused on core functionality. The codebase is intentionally simple and easy to debug.
