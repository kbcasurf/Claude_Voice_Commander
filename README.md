# Claude Voice Commander 🎤

A voice automation system that allows hands-free operation of Claude Code CLI through speech commands. Speak naturally and control Claude without touching your keyboard!

## Features

- 🎤 **Real-time Voice Recognition** - Uses local Whisper with faster-whisper for instant speech-to-text
- ⚡ **Live Text Display** - Words appear on screen as you speak, like typing in real-time
- ⌨️ **Direct CLI Integration** - Simulates keyboard input to the actual Claude CLI terminal
- 🎯 **Smart Command Processing** - Converts natural speech to Claude commands
- 🔧 **Mode Control** - Switch between plan mode, auto mode, and interactive mode with voice
- 🔢 **Option Selection** - Select numbered options by speaking "option one", "select two", etc.
- ✅ **Confirmation Handling** - Say "yes", "no", "accept", or "cancel" for confirmations
- 👀 **Visual Feedback** - See exactly what's happening with the Claude CLI interface
- 🚀 **Ultra-Low Latency** - Local processing with streaming recognition
- 🔇 **No API Dependencies** - Completely offline speech recognition

## Architecture

The system works by:
1. Capturing audio from your microphone in real-time
2. Converting speech to text using Whisper
3. Processing voice commands and mapping them to Claude CLI actions
4. Sending keystrokes directly to the Claude CLI terminal process
5. Providing visual and audio feedback

This approach preserves the full Claude CLI experience while adding voice control on top.

## Installation

### Prerequisites
- Python 3.8 or higher
- Claude Code CLI installed and accessible
- Microphone access
- Operating system: Linux, macOS, or Windows

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Configuration
The system uses local Whisper by default - **no API keys needed!**

**Optimized for CPU-only systems:**

1. **Model size options (tiny is default for speed):**
```bash
export WHISPER_MODEL_SIZE=tiny    # Fastest, still accurate
export WHISPER_MODEL_SIZE=base    # Better accuracy, slower
export WHISPER_MODEL_SIZE=small   # Even better accuracy
```

2. **Optional: Audio device selection:**
```bash
export AUDIO_DEVICE_INDEX=0  # Specific microphone device
```

## Usage

### Basic Usage
```bash
python main.py
```

The system will:
1. Start Claude CLI in a new terminal session
2. Begin listening for voice commands
3. Display status information and feedback

### Voice Commands

#### Mode Switching
- "Plan mode" - Switch to planning mode
- "Auto mode" / "Auto accept" - Switch to automatic mode  
- "Interactive mode" / "Ask before apply" - Switch to interactive mode

#### Option Selection
- "Option one" / "Select one" - Select option 1
- "Option two" / "Select two" - Select option 2
- etc.

#### Confirmations
- "Yes" / "Accept" / "Confirm" - Confirm action
- "No" / "Cancel" / "Reject" - Cancel action

#### File Operations
- "Open file example.py"
- "Create new file main.js"
- "Show directory contents"

#### Code Operations
- "Run the tests"
- "Build the project"
- "Debug this function"

#### Search Operations
- "Search for function getName"
- "Find all TODO comments"

#### Git Operations
- "Git status"
- "Git commit with message added new feature"
- "Git push changes"

#### General Queries
- "Explain this code"
- "How does this function work?"
- "What are the available commands?"

## Configuration

The system can be configured through environment variables or a config file:

### Environment Variables
- `OPENAI_API_KEY` - OpenAI API key for Whisper
- `WHISPER_USE_LOCAL` - Use local Whisper model (true/false)
- `WHISPER_MODEL` - Local model size (base, small, medium, large)
- `CLAUDE_CLI_PATH` - Path to Claude CLI executable
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `DEBUG_MODE` - Enable debug mode (true/false)

### Config File
Create `voice_commander.config` for persistent settings (JSON format):
```json
{
  "audio": {
    "sample_rate": 16000,
    "silence_threshold": 0.01
  },
  "whisper": {
    "model": "base",
    "use_local": true
  },
  "feedback": {
    "enable_audio": true,
    "voice_feedback": false
  }
}
```

## Development

### Project Structure
```
src/
├── __init__.py
├── config.py              # Configuration management
├── voice_commander.py     # Main orchestrator
├── audio_capture.py       # Real-time audio capture
├── speech_to_text.py      # Whisper integration
├── command_processor.py   # Command parsing and intent recognition
├── terminal_controller.py # Claude CLI interaction
└── feedback_system.py     # User feedback
```

### Running Tests
```bash
pytest tests/
```

### Development Installation
```bash
pip install -e .
```

## Troubleshooting

### Common Issues

**Audio not being captured:**
- Check microphone permissions
- Verify audio device in system settings
- Try different sample rates in config

**Claude CLI not found:**
- Ensure Claude CLI is installed and in PATH
- Set `CLAUDE_CLI_PATH` environment variable

**Whisper API errors:**
- Verify OpenAI API key is set
- Check internet connection
- Consider using local Whisper model

**Low recognition accuracy:**
- Speak clearly and at moderate pace
- Reduce background noise
- Adjust silence threshold in config

### Debug Mode
Enable debug mode for detailed logging:
```bash
export DEBUG_MODE=true
python main.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- OpenAI Whisper for speech recognition
- Anthropic Claude for the amazing CLI tool
- The Python community for excellent libraries