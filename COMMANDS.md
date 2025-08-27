# Voice Commander - Keyphrase Commands Reference

## Overview
Claude Voice Commander acts as a voice-controlled keyboard for Claude Code CLI. It starts in **SLEEPING** mode for safety - you must activate it first. Once activated, speak naturally and your words appear in real-time in the Claude terminal, with special keyphrases triggering keyboard actions.

## Voice Commands

### 🎤 Voice Activation Control
| Keyphrase | Action | Description |
|-----------|---------|-------------|
| `"activate voice commander"` | Wake up | Start listening for all commands |
| `"start voice commander"` | Wake up | Start listening for all commands |
| `"stop voice commander"` | Sleep | Only listen for activation commands |
| `"deactivate voice commander"` | Sleep | Only listen for activation commands |

### 📝 Text Input (when activated)
- **Any spoken text** → Types directly into Claude terminal in real-time
- Text appears as you speak, just like typing on a keyboard

### ✅ Send Commands
| Keyphrase | Keyboard Action | Description |
|-----------|----------------|-------------|
| `"send this prompt"` | `Enter` | Executes the typed command |
| `"send prompt"` | `Enter` | Executes the typed command |

### ✏️ Editing Commands
| Keyphrase | Keyboard Action | Description |
|-----------|----------------|-------------|
| `"remove last word"` | `Alt+Backspace` | Removes the last word typed |
| `"remove this line"` | `Ctrl+U` | Clears the current line |
| `"remove complete input"` | `Ctrl+U` | Clears the current line |
| `"start over"` | `Ctrl+A, Delete` | Clears all text |

### 🔢 Option Selection
| Keyphrase | Keyboard Action | Description |
|-----------|----------------|-------------|
| `"select option 1"` | `1` | Selects option 1 in Claude |
| `"select option 2"` | `2` | Selects option 2 in Claude |
| `"select option 3"` | `3` | Selects option 3 in Claude |
| `"select option 4"` | `4` | Selects option 4 in Claude |

### 🔄 Mode Control
| Keyphrase | Keyboard Action | Description |
|-----------|----------------|-------------|
| `"change operation mode"` | `Shift+Tab` | Changes Claude's operation mode |

## Usage Examples

### Getting Started
```
System starts in SLEEPING mode for safety
Say: "activate voice commander"
     → Voice Commander wakes up and starts listening
```

### Basic Text Input and Send
```
Say: "Create a Python function that calculates fibonacci"
     → Text types in Claude terminal
Say: "send this prompt"  
     → Presses Enter to execute
```

### Editing While Speaking
```
Say: "Write a function to calculate prime numbers"
     → Text appears in terminal
Say: "remove last word"
     → Removes "numbers"
Say: "factors"
     → Types "factors"
Say: "send this prompt"
     → Executes command
```

### Selecting Options
```
Claude shows: "How would you like to proceed?
              1. Option one
              2. Option two"
Say: "select option 2"
     → Presses '2' to select option two
```

### Changing Mode
```
Say: "change operation mode"
     → Presses Shift+Tab to cycle through Claude's modes
```

### Stopping Voice Commander
```
Say: "stop voice commander"
     → Goes back to SLEEPING mode - only listens for activation
     → Ignores all other speech until reactivated
```

## Tips
- **Always start with activation**: System starts SLEEPING - say "activate voice commander" first
- Speak clearly at a moderate pace
- The confidence threshold is set to 0.3 for better recognition
- All text appears in real-time when ACTIVE - no need to wait
- Use editing commands to correct mistakes without restarting
- Say keyphrases distinctly to trigger actions
- **Deactivate when done**: Say "stop voice commander" to prevent accidental commands

## Technical Details
- **Voice activation**: Starts in SLEEPING mode, only wakes on specific keyphrases
- **Real-time typing**: Text is sent directly to terminal via xdotool
- **Keyboard simulation**: Commands send actual keyboard shortcuts
- **Voice recognition**: Uses local Whisper model (tiny by default)
- **Target window**: Captured during 5-second setup countdown