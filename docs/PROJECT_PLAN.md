# Letta Chat Client - Project Plan

## Project Overview
A simple, clean chat client for Letta AI agents. Focus on core functionality first, then add polish.

## Core Requirements
1. **Connect to Letta server** using pre-configured credentials
2. **Send messages** to a specific agent
3. **Receive responses** in real-time
4. **Simple text interface** - no complex UI initially
5. **Error handling** for common issues

## Architecture

### Phase 1: Minimal Viable Product (MVP)
```
simple_chat.py          # Main application entry point
config.py              # Configuration management (.env)
letta_client.py        # Letta API wrapper (minimal)
```

### Phase 2: Basic Features
```
error_handler.py       # Centralized error handling
```

### Phase 3: Polish (Optional)
```
tui_interface.py       # Textual TUI (if needed)
```

## File Structure
```
TUI-chat/
├── docs/
│   ├── PROJECT_PLAN.md
│   └── letta-api-reference.md
├── simple_chat.py      # Main app
├── config.py          # Config management (idempotent)
├── letta_client.py    # API wrapper
├── requirements.txt   # Dependencies
├── .env.example      # Environment template
└── README.md         # Setup instructions
```

## Implementation Plan

### Step 1: Basic Configuration
- [ ] Create `config.py` for environment variables (idempotent)
- [ ] Create `.env.example` template
- [ ] Test configuration loading

### Step 2: Letta API Wrapper
- [ ] Create minimal `letta_client.py`
- [ ] Implement connection testing
- [ ] Implement message sending (sync)
- [ ] Implement message streaming (async)
- [ ] Test with actual Letta server

### Step 3: Simple Chat Interface
- [ ] Create `simple_chat.py` with basic input/output
- [ ] Implement command handling (/help, /quit, etc.)
- [ ] Add error handling and user feedback
- [ ] Test end-to-end functionality

### Step 4: Optional Enhancements
- [ ] Add agent selection (store in .env)
- [ ] Add configuration validation
- [ ] Add logging

## Dependencies (Minimal)
```
letta-client          # Official Letta Python SDK
python-dotenv         # Environment variable loading
```

## Design Principles
1. **Keep it simple** - No over-engineering, no database, no web interface
2. **Fail fast** - Clear error messages
3. **One thing well** - Focus on core chat functionality
4. **Easy to debug** - Clear logging and error handling
5. **Store in .env** - All configuration and state in environment variables
6. **Idempotent** - Can be run multiple times without issues

## Success Criteria
- [ ] Can connect to Letta server
- [ ] Can send messages and receive responses
- [ ] Clear error messages when things go wrong
- [ ] Easy to run with `python simple_chat.py`
- [ ] Code is clean and well-documented

## Notes
- Start with the absolute minimum needed to chat
- Add features incrementally
- Test each step before moving to the next
- Keep the codebase small and focused
