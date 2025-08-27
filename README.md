# Claude Voice Commander 🎤

A voice automation system that allows hands-free operation of Claude Code CLI through speech commands. Uses local Whisper for speech recognition and targets any terminal window through focus-based control.

## Features

- 🎤 **Local Voice Recognition** - Uses faster-whisper for offline speech-to-text processing
- 🎯 **Universal Terminal Control** - Works with any focused terminal window using xdotool
- 📝 **Smart Text Accumulation** - Speak your request in parts, combine with finalization keywords
- 🔧 **Claude CLI Mode Control** - Voice commands for plan/auto/interactive modes
- 🔢 **Quick Option Selection** - Say "option one" through "option five" for numbered choices
- ✅ **Voice Confirmations** - "yes"/"no" responses for Claude prompts
- 🖥️ **Window Targeting** - 10-second countdown to capture your target terminal
- 🔇 **No API Dependencies** - Completely offline speech recognition
- ⚡ **Direct Keyboard Simulation** - Sends actual keystrokes to focused applications

## Architecture

The system works by:
1. Capturing audio from your microphone 
2. Converting speech to text using local Whisper
3. Processing voice commands with intelligent text accumulation
4. Targeting any terminal window through xdotool focus capture
5. Sending keyboard input directly to the targeted application

This approach works with any terminal application, preserving native functionality while adding voice control.

## Installation

### Prerequisites
- Python 3.8 or higher
- Claude Code CLI installed and accessible in your target terminal
- Microphone access
- Linux system with xdotool installed (`sudo apt install xdotool`)

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Configuration
The system uses local Whisper by default - **no API keys needed!**

**Whisper model options (tiny is default for speed):**
```bash
export WHISPER_MODEL_SIZE=tiny    # Fastest, still accurate
export WHISPER_MODEL_SIZE=base    # Better accuracy, slower  
export WHISPER_MODEL_SIZE=small   # Even better accuracy
```

**Optional settings:**
```bash
export AUDIO_DEVICE_INDEX=0  # Specific microphone device
export DEBUG_MODE=true       # Enable detailed logging
```

## Usage

### Basic Usage
```bash
python main.py
```

The system will:
1. Give you 5 seconds to focus on your target terminal (where Claude CLI is running)
2. Capture the focused window for keyboard input targeting
3. Begin listening for voice commands

### Voice Commands

**See COMMAND.md for complete operational reference**


## Configuration

The system can be configured through environment variables:

### Environment Variables
- `WHISPER_MODEL_SIZE` - Model size (tiny, base, small, medium, large)
- `WHISPER_DEVICE` - Processing device (cpu, cuda, auto)
- `WHISPER_COMPUTE_TYPE` - Computation type (int8, float16, float32)
- `AUDIO_DEVICE_INDEX` - Specific microphone device index
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
├── config.py                     # Configuration management
├── voice_commander.py            # Main orchestrator
├── audio_capture.py              # Real-time audio capture  
├── speech_to_text.py             # Whisper integration
├── command_processor.py          # Command parsing and text accumulation
├── universal_terminal_controller.py # xdotool-based terminal control
└── feedback_system.py            # User feedback
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
- Try different `AUDIO_DEVICE_INDEX` values

**xdotool not working:**
- Install xdotool: `sudo apt install xdotool`
- Verify X11 display is available
- Check if running in Wayland (xdotool requires X11)

**Commands not reaching Claude:**
- Ensure target terminal was properly focused during 10-second countdown
- Check that Claude CLI is running in the captured window
- Try recapturing window by restarting the application

**Low recognition accuracy:**
- Speak clearly at moderate pace
- Reduce background noise
- Use exact phrases from GUIDE.md for best results

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