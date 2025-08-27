# Claude Voice Commander - Operational Guide

## Quick Start
1. Run `python main.py`
2. Focus on terminal with Claude CLI running (10-second countdown)
3. Start speaking commands

## Voice Commands Reference

### Claude CLI Mode Control
| Voice Command | Action |
|---------------|--------|
| `"plan mode"` | Switch to plan mode (`/plan`) |
| `"planning mode"` | Switch to plan mode (`/plan`) |
| `"auto mode"` | Switch to auto mode (`/auto`) |
| `"auto accept"` | Switch to auto mode (`/auto`) |
| `"interactive mode"` | Switch to interactive mode (`/interactive`) |
| `"ask before apply"` | Switch to interactive mode (`/interactive`) |

### Option Selection
| Voice Command | Sends |
|---------------|-------|
| `"option one"` / `"select one"` | `1` |
| `"option two"` / `"select two"` | `2` |
| `"option three"` / `"select three"` | `3` |
| `"option four"` / `"select four"` | `4` |
| `"option five"` / `"select five"` | `5` |

### Confirmations
| Voice Command | Sends |
|---------------|-------|
| `"yes"` / `"accept"` / `"continue"` | `y` |
| `"no"` / `"cancel"` / `"reject"` | `n` |
| `"quit"` / `"exit"` | `q` |
| `"help"` | `h` |

## Text Accumulation System

### How It Works
1. **Start Speaking**: Say any non-control command → system starts accumulating text
2. **Continue Speaking**: Keep adding to your request → text gets combined
3. **Finalize**: Say a finalization keyword → sends complete request to Claude

### Finalization Keywords
- `"send to claude"`
- `"execute command"`
- `"process request"`
- `"submit"`

### Example Usage
```
You: "Create a new Python function"
System: [ACCUMULATING] Create a new Python function
You: "that calculates the factorial of a number"
System: [ADDED] that calculates the factorial of a number
System: [FULL TEXT] Create a new Python function that calculates the factorial of a number
You: "send to claude"
System: → Sends complete request to Claude CLI
```

## Voice Command Patterns

### File Operations
| Voice Pattern | Example | Generated Command |
|---------------|---------|-------------------|
| `"open file [filename]"` | "open file main.py" | "Open and edit the file main.py" |
| `"create file [filename]"` | "create file test.js" | "Create a new file named test.js" |
| `"show directory contents"` | - | "Show the current directory contents" |

### Code Operations
| Voice Pattern | Example | Generated Command |
|---------------|---------|-------------------|
| `"run [target]"` | "run tests" | "Run tests" |
| `"build [target]"` | "build project" | "Build the project" |
| `"debug [target]"` | "debug function" | "Debug and fix function" |

### Git Operations
| Voice Pattern | Example | Generated Command |
|---------------|---------|-------------------|
| `"git status"` | - | "Show git status" |
| `"git commit [message]"` | "git commit added feature" | "Git commit with message: added feature" |
| `"git push"` | - | "Git push changes" |

### Search Operations
| Voice Pattern | Example | Generated Command |
|---------------|---------|-------------------|
| `"find [term]"` | "find function getName" | "Search for 'function getName' in the codebase" |
| `"search for [term] in [location]"` | "search for TODO in src" | "Search for 'TODO' in src" |

## Speech Recognition Tips

### For Best Recognition
- **Speak clearly** at moderate pace
- **Use natural pauses** between command parts
- **Avoid background noise** when possible
- **Use consistent phrases** from the command tables

### Common Speech Corrections
The system automatically corrects:
- "clause" → "claude"
- "clawed" → "claude" 
- "called" → "claude"
- "dot py" → ".py"
- "dot js" → ".js"

### Number Words
| Word | Converts To |
|------|-------------|
| "one" | "1" |
| "two" | "2" |
| "three" | "3" |
| "four" | "4" |
| "five" | "5" |

## Workflow Examples

### Simple Command
```
You: "git status"
System: → Immediately sends "Show git status" to Claude
```

### Complex Request (Text Accumulation)
```
You: "Write a Python function"
System: [ACCUMULATING] Write a Python function
You: "that reads a CSV file"
System: [ADDED] that reads a CSV file  
You: "and returns the data as a dictionary"
System: [ADDED] and returns the data as a dictionary
You: "execute command"
System: → Sends complete request to Claude
```

### Mode Switching
```
You: "plan mode"
System: → Sends "/plan" to Claude CLI
You: "Create a REST API endpoint"
System: [ACCUMULATING] Create a REST API endpoint
You: "send to claude"
System: → Sends request to Claude (will create plan instead of executing)
```

## Error Recovery

### If Command Not Recognized
- **Speak more clearly** and try again
- **Use exact phrases** from command tables
- **Check if accumulation is active** - say finalization keyword first

### If Wrong Mode
- **Switch modes** with voice: "auto mode", "plan mode", "interactive mode"
- **Use shortcuts**: "yes" for accept, "no" for cancel

### If System Unresponsive
- **Check terminal focus** - system sends to focused window from startup
- **Restart application** if needed
- **Check microphone** permissions and settings