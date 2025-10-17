# Animus Chat - Enhanced TUI Chat Client

A beautiful, modern terminal user interface (TUI) for interacting with Letta AI agents. Features a clean VS Code-inspired design with enhanced user experience for seamless agent conversations.

## 🚀 Features

- **Modern TUI Interface**: Beautiful VS Code-inspired terminal interface with clean design
- **Real-time Streaming**: Live token-by-token response streaming from Letta agents  
- **Enhanced Message Display**: Styled message boxes with user names and timestamps
- **Agent Management**: Easy agent selection with visual command menu
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Responsive Design**: Smooth resizing and adaptive layout
- **Keyboard Shortcuts**: Convenient hotkeys for common actions (Ctrl+N, Ctrl+H, etc.)
- **Professional Styling**: Clean borders, proper spacing, and modern color palette
- **Comprehensive Testing**: 100% test coverage on core functionality

## 📋 Requirements

- Python 3.8+
- Letta API access (server URL and API token)
- Internet connection

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/AnimusUNO/animus-chat.git
cd animus-chat
```

### 2. Set Up Virtual Environment

   ```bash
# Create virtual environment
   python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

   ```bash
# Install main dependencies
   pip install -r requirements.txt

# Install test dependencies (optional)
pip install -r requirements-test.txt
```

### 4. Configure Environment

```bash
# Run the configuration script to set up your .env file
python config.py
```

The configuration script will:
- Create a `.env` file from the template
- Prompt you for your Letta server URL and API token
- Set up your display name and default agent
- Validate your configuration

**Required Information:**
- **Letta Server URL**: Your Letta server endpoint (e.g., `https://your-letta-server.com:8283`)
- **API Token**: Your Letta API authentication token
- **Display Name**: Your preferred name in chat (optional, defaults to "User")
- **Default Agent ID**: Your preferred agent ID (optional)

## 🎯 Usage

### Start the Chat Client

```bash
python main.py
```

### Available Commands

- `/help` - Show available commands
- `/status` - Display connection status and current agent
- `/agents` - List all available agents
- `/agent <id>` or `/agent <number>` - Switch to specific agent
- `/clear` - Clear the screen
- `/quit` - Exit the application

### Example Session

```
============================================================
           LETTA SIMPLE CHAT CLIENT
============================================================

Testing connection to Letta server...
Connected successfully!
Fetching available agents...
Found 10 agents:
  1. IncredibleBroccoli (ID: agent-c1e3ba04-7dd5-4c36-8ae8-96b476b6eaa8)
  2. Puddy the Bear (ID: agent-add8c834-1677-4d81-a3d0-7d6d68b55262)
  ...

Set agent: agent-8d3f7375-9bb5-446a-924d-89962e7f97d3

Server: https://sanctum.zero1.network
User: YourName
Agent: Iris (agent-8d3f7375-9bb5-446a-924d-89962e7f97d3)
------------------------------------------------------------

[YourName] Hello, how are you today?
[Iris] Hello! I'm doing well, thank you for asking. I'm here and ready to help you with whatever you need. How are you doing today? Is there anything specific I can assist you with?

[YourName] /agent 2
Set agent: Puddy the Bear (agent-add8c834-1677-4d81-a3d0-7d6d68b55262)

[YourName] Tell me a story
[Puddy the Bear] Once upon a time, in a cozy little forest...
```

## 🧪 Testing

### Run All Tests

```bash
python run_tests.py
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/test_config.py tests/test_letta_client.py

# Integration tests
pytest tests/test_integration.py

# End-to-end tests
pytest tests/test_simple_chat.py

# With coverage report
pytest --cov=simple_chat --cov-report=html
```

### Test Coverage

The project maintains 100% test coverage on `simple_chat.py` and comprehensive coverage across all modules:

- **Unit Tests**: Individual component testing
- **Integration Tests**: Module interaction testing  
- **End-to-End Tests**: Full application workflow testing

## 📁 Project Structure

```
animus-chat/
├── docs/                    # Documentation
│   ├── PROJECT_PLAN.md     # Development roadmap
│   └── letta-api-reference.md
├── tests/                   # Test suite
│   ├── conftest.py         # Test fixtures
│   ├── test_config.py      # Config module tests
│   ├── test_integration.py # Integration tests
│   ├── test_letta_client.py # API client tests
│   └── test_simple_chat.py # Main app tests
├── config.py               # Configuration management
├── letta_api.py           # Letta API wrapper
├── main.py                # Application entry point
├── simple_chat.py         # Core chat interface
├── requirements.txt       # Main dependencies
├── requirements-test.txt  # Test dependencies
├── pytest.ini            # Pytest configuration
├── run_tests.py          # Test runner script
├── env.example           # Environment template
└── README.md             # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `LETTA_SERVER_URL` | Letta server endpoint | Yes | - |
| `LETTA_API_TOKEN` | API authentication token | Yes | - |
| `DISPLAY_NAME` | Your display name in chat | No | "User" |
| `DEFAULT_AGENT_ID` | Preferred agent ID | No | - |

### Configuration Features

- **Idempotent**: Safe to run `config.py` multiple times
- **Validation**: Checks for required values and valid URLs
- **Auto-save**: Automatically saves configuration to `.env`
- **Error Handling**: Clear error messages for configuration issues

## 🚀 Development

### Setting Up Development Environment

```bash
# Clone and setup
git clone https://github.com/AnimusUNO/animus-chat.git
cd animus-chat
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
pip install -r requirements-test.txt

# Run tests to verify setup
python run_tests.py
```

### Code Style

- Follow PEP 8 Python style guidelines
- Use type hints where appropriate
- Write comprehensive docstrings
- Maintain 100% test coverage on core modules

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`python run_tests.py`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 🐛 Troubleshooting

### Common Issues

**Connection Failed**
- Run `python config.py` to reconfigure your settings
- Verify `LETTA_SERVER_URL` is correct
- Check `LETTA_API_TOKEN` is valid
- Ensure internet connection is working

**Agent Not Found**
- Use `/agents` to see available agents
- Check agent ID is correct
- Try using agent number instead of ID

**Unicode/Emoji Issues on Windows**
- The app includes Windows-compatible emoji handling
- If issues persist, check console font supports Unicode

**Test Failures**
- Ensure virtual environment is activated
- Install all test dependencies: `pip install -r requirements-test.txt`
- Check `.env` file exists with valid configuration

### Debug Mode

For detailed debugging, you can modify the logging level in the source code or add debug prints.

## 📄 License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0) for all code. Documentation and other non-code content is licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC-BY-SA-4.0).

- **Code License**: [AGPL-3.0](LICENSE-CODE)
- **Documentation License**: [CC-BY-SA-4.0](LICENSE-DOCS)

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/AnimusUNO/animus-chat/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AnimusUNO/animus-chat/discussions)
- **Documentation**: See `docs/` folder for detailed documentation

## 🙏 Acknowledgments

- Built for the [Letta AI](https://letta.ai) ecosystem
- Inspired by the need for simple, developer-friendly AI chat interfaces
- Thanks to the Python community for excellent testing tools

---

**Made with ❤️ for developers who prefer the command line**