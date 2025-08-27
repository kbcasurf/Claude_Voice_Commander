"""Command processing and validation module."""

import asyncio
import logging
import re
from typing import Optional, Callable, Dict, List
from dataclasses import dataclass


@dataclass
class CommandIntent:
    """Represents a recognized command intent."""
    intent: str
    confidence: float
    parameters: Dict[str, str]
    original_text: str


class CommandProcessor:
    """Processes and validates voice commands."""
    
    def __init__(self):
        """Initialize command processor."""
        self.logger = logging.getLogger(__name__)
        
        # Event handlers
        self.on_command_validated: Optional[Callable[[str, str, float], None]] = None
        self.on_error: Optional[Callable[[str, Exception], None]] = None
        self.on_text_accumulation_started: Optional[Callable[[str], None]] = None
        self.on_text_accumulated: Optional[Callable[[str, str], None]] = None
        
        # Command patterns and intents
        self.command_patterns = self._initialize_patterns()
        self.confidence_threshold = 0.7
        
        # Text concatenation state
        self.accumulated_text = ""
        self.is_accumulating = False
        self.finalization_keywords = ["send to claude", "execute command", "process request", "submit"]
        
        # Special command patterns for Claude CLI control
        self.claude_control_patterns = {
            "mode_switch": [
                r"(?:switch to|enter|go to|use)\s+(plan|planning|auto|automatic|interactive|ask)\s*mode",
                r"(plan|auto|interactive)\s*mode",
                r"auto\s*accept",
                r"ask\s*before\s*apply"
            ],
            "selection": [
                r"(?:select|choose|pick)\s+(?:option\s+)?(\d+|one|two|three|four|five)",
                r"option\s+(\d+|one|two|three|four|five)",
                r"number\s+(\d+)"
            ],
            "confirmation": [
                r"(?:yes|accept|confirm|ok|okay|continue)",
                r"(?:no|reject|cancel|abort|stop)"
            ]
        }
    
    def _initialize_patterns(self) -> Dict[str, List[str]]:
        """Initialize command patterns for intent recognition."""
        return {
            "file_operation": [
                r"(?:open|edit|read|show|display)\s+(?:file\s+)?(.+)",
                r"(?:create|make|new)\s+(?:file\s+)?(.+)",
                r"(?:save|write)\s+(?:file\s+)?(.+)?",
                r"(?:delete|remove)\s+(?:file\s+)?(.+)"
            ],
            "code_operation": [
                r"(?:run|execute|start)\s+(.+)",
                r"(?:build|compile)\s+(.+)?",
                r"(?:test|check)\s+(.+)?",
                r"(?:debug|fix)\s+(.+)?"
            ],
            "search_operation": [
                r"(?:find|search|look for)\s+(.+)",
                r"(?:grep|search for)\s+(.+)\s+in\s+(.+)",
                r"(?:show|list)\s+(?:files|directories|functions)\s*(?:in\s+(.+))?"
            ],
            "git_operation": [
                r"(?:git\s+)?(?:commit|stage|add)\s*(.+)?",
                r"(?:git\s+)?(?:status|diff|log)\s*(.+)?",
                r"(?:git\s+)?(?:push|pull|checkout)\s*(.+)?"
            ],
            "general_query": [
                r"(?:what|how|why|where|when)\s+(.+)",
                r"(?:explain|describe|tell me about)\s+(.+)",
                r"(?:help|assist|show help)\s*(?:with\s+(.+))?"
            ]
        }
    
    async def process_text(self, text: str, confidence: float):
        """Process recognized text and extract command intent."""
        try:
            self.logger.debug(f"Processing text: '{text}' (confidence: {confidence})")
            
            if confidence < self.confidence_threshold:
                self.logger.warning(f"Low confidence recognition: {confidence}")
                return
            
            # Clean and normalize text
            normalized_text = self._normalize_text(text)
            
            # Check if this is a finalization keyword
            if self._is_finalization_command(normalized_text):
                if self.is_accumulating and self.accumulated_text.strip():
                    # Send accumulated text to Claude
                    final_command = self.accumulated_text.strip()
                    self.logger.info(f"Finalizing accumulated command: '{final_command}'")
                    
                    if self.on_command_validated:
                        await self.on_command_validated(final_command, "accumulated_text", 1.0)
                    
                    # Reset accumulation state
                    self.accumulated_text = ""
                    self.is_accumulating = False
                else:
                    self.logger.warning("Finalization keyword detected but no accumulated text")
                return
            
            # Check for special Claude control commands first
            control_intent = self._extract_control_intent(normalized_text)
            
            if control_intent:
                # Handle control commands immediately (don't accumulate)
                command = self._generate_command(control_intent)
                if command and self.on_command_validated:
                    await self.on_command_validated(command, control_intent.intent, control_intent.confidence)
                return
            
            # For all other text, accumulate it
            if not self.is_accumulating:
                # Start accumulating
                self.is_accumulating = True
                self.accumulated_text = normalized_text
                self.logger.info(f"Started text accumulation: '{normalized_text}'")
                
                # Trigger accumulation started event
                if self.on_text_accumulation_started:
                    await self.on_text_accumulation_started(normalized_text)
            else:
                # Add to accumulated text
                self.accumulated_text += " " + normalized_text
                self.logger.info(f"Added to accumulated text: '{normalized_text}' -> Full: '{self.accumulated_text}'")
                
                # Trigger text accumulated event
                if self.on_text_accumulated:
                    await self.on_text_accumulated(normalized_text, self.accumulated_text)
                
        except Exception as e:
            self.logger.error(f"Error processing text: {e}")
            if self.on_error:
                await self.on_error("CommandProcessor", e)
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for better processing."""
        # Convert to lowercase and remove extra spaces
        normalized = re.sub(r'\s+', ' ', text.lower().strip())
        
        # Handle common speech recognition errors
        replacements = {
            "clause": "claude",
            "clawed": "claude", 
            "called": "claude",
            "file name": "filename",
            "dot py": ".py",
            "dot js": ".js",
            "dot json": ".json"
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        return normalized
    
    def _is_finalization_command(self, text: str) -> bool:
        """Check if the text contains a finalization keyword."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.finalization_keywords)
    
    def _extract_control_intent(self, text: str) -> Optional[CommandIntent]:
        """Extract only Claude control command intents (for immediate processing)."""
        # Only check for Claude CLI control patterns
        for intent_type, patterns in self.claude_control_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    parameters = {}
                    groups = match.groups()
                    
                    if intent_type == "mode_switch" and groups:
                        mode = groups[0].lower()
                        if mode in ["planning"]: mode = "plan"
                        if mode in ["automatic"]: mode = "auto"
                        if mode in ["ask"]: mode = "interactive"
                        parameters["mode"] = mode
                    elif intent_type == "selection" and groups:
                        selection = groups[0].lower()
                        # Convert word numbers to digits
                        number_map = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5"}
                        parameters["selection"] = number_map.get(selection, selection)
                    elif intent_type == "confirmation":
                        parameters["response"] = "yes" if any(word in text.lower() for word in ["yes", "accept", "confirm", "ok", "okay", "continue"]) else "no"
                    
                    return CommandIntent(
                        intent=f"claude_control_{intent_type}",
                        confidence=0.95,  # High confidence for control commands
                        parameters=parameters,
                        original_text=text
                    )
        
        return None
    
    def _extract_intent(self, text: str) -> Optional[CommandIntent]:
        """Extract command intent from normalized text."""
        # First check for Claude CLI control patterns
        for intent_type, patterns in self.claude_control_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    parameters = {}
                    groups = match.groups()
                    
                    if intent_type == "mode_switch" and groups:
                        mode = groups[0].lower()
                        if mode in ["planning"]: mode = "plan"
                        if mode in ["automatic"]: mode = "auto"
                        if mode in ["ask"]: mode = "interactive"
                        parameters["mode"] = mode
                    elif intent_type == "selection" and groups:
                        selection = groups[0].lower()
                        # Convert word numbers to digits
                        number_map = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5"}
                        parameters["selection"] = number_map.get(selection, selection)
                    elif intent_type == "confirmation":
                        parameters["response"] = "yes" if any(word in text.lower() for word in ["yes", "accept", "confirm", "ok", "okay", "continue"]) else "no"
                    
                    return CommandIntent(
                        intent=f"claude_control_{intent_type}",
                        confidence=0.95,  # High confidence for control commands
                        parameters=parameters,
                        original_text=text
                    )
        
        # Then check for general command patterns
        for intent_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    parameters = {}
                    groups = match.groups()
                    
                    # Extract parameters based on intent type
                    if intent_type == "file_operation" and groups:
                        parameters["file_path"] = groups[0].strip()
                    elif intent_type == "search_operation" and groups:
                        parameters["search_term"] = groups[0].strip()
                        if len(groups) > 1 and groups[1]:
                            parameters["search_location"] = groups[1].strip()
                    elif groups:
                        parameters["target"] = groups[0].strip() if groups[0] else ""
                    
                    return CommandIntent(
                        intent=intent_type,
                        confidence=0.9,  # Pattern-based confidence
                        parameters=parameters,
                        original_text=text
                    )
        
        return None
    
    def _generate_command(self, intent: CommandIntent) -> Optional[str]:
        """Generate Claude CLI command from intent."""
        try:
            # Handle Claude control commands
            if intent.intent.startswith("claude_control_"):
                return self._generate_control_command(intent)
            elif intent.intent == "file_operation":
                return self._generate_file_command(intent)
            elif intent.intent == "code_operation":
                return self._generate_code_command(intent)
            elif intent.intent == "search_operation":
                return self._generate_search_command(intent)
            elif intent.intent == "git_operation":
                return self._generate_git_command(intent)
            elif intent.intent == "general_query":
                return self._generate_query_command(intent)
            else:
                return intent.original_text  # Fallback to original text
                
        except Exception as e:
            self.logger.error(f"Error generating command: {e}")
            return None
    
    def _generate_control_command(self, intent: CommandIntent) -> str:
        """Generate Claude CLI control command."""
        control_type = intent.intent.replace("claude_control_", "")
        
        if control_type == "mode_switch":
            mode = intent.parameters.get("mode", "")
            if "auto" in intent.original_text:
                return "auto accept"
            elif "plan" in intent.original_text:
                return "plan mode"
            elif "interactive" in intent.original_text or "ask" in intent.original_text:
                return "ask before apply"
            return f"{mode} mode"
        
        elif control_type == "selection":
            selection = intent.parameters.get("selection", "")
            return f"select {selection}"
        
        elif control_type == "confirmation":
            response = intent.parameters.get("response", "")
            return response
        
        return intent.original_text
    
    def _generate_file_command(self, intent: CommandIntent) -> str:
        """Generate file operation command."""
        text = intent.original_text
        file_path = intent.parameters.get("file_path", "")
        
        if "open" in text or "edit" in text or "show" in text:
            return f"Open and edit the file {file_path}" if file_path else "Show the current directory contents"
        elif "create" in text or "new" in text:
            return f"Create a new file named {file_path}" if file_path else "Create a new file"
        elif "save" in text:
            return f"Save the current file" + (f" as {file_path}" if file_path else "")
        elif "delete" in text or "remove" in text:
            return f"Delete the file {file_path}" if file_path else "Show files that can be deleted"
        else:
            return f"Work with file {file_path}" if file_path else "Show file operations"
    
    def _generate_code_command(self, intent: CommandIntent) -> str:
        """Generate code operation command."""
        text = intent.original_text
        target = intent.parameters.get("target", "")
        
        if "run" in text or "execute" in text:
            return f"Run {target}" if target else "Run the current project"
        elif "build" in text or "compile" in text:
            return f"Build {target}" if target else "Build the project"
        elif "test" in text:
            return f"Test {target}" if target else "Run tests"
        elif "debug" in text or "fix" in text:
            return f"Debug and fix {target}" if target else "Debug the current issue"
        else:
            return f"Execute code operation: {text}"
    
    def _generate_search_command(self, intent: CommandIntent) -> str:
        """Generate search operation command."""
        search_term = intent.parameters.get("search_term", "")
        location = intent.parameters.get("search_location", "")
        
        if location:
            return f"Search for '{search_term}' in {location}"
        else:
            return f"Search for '{search_term}' in the codebase"
    
    def _generate_git_command(self, intent: CommandIntent) -> str:
        """Generate git operation command."""
        text = intent.original_text
        target = intent.parameters.get("target", "")
        
        if "commit" in text or "stage" in text:
            return f"Git commit with message: {target}" if target else "Git status and commit changes"
        elif "status" in text:
            return "Show git status"
        elif "diff" in text:
            return "Show git diff"
        elif "push" in text:
            return "Git push changes"
        elif "pull" in text:
            return "Git pull latest changes"
        else:
            return f"Git operation: {text}"
    
    def _generate_query_command(self, intent: CommandIntent) -> str:
        """Generate general query command."""
        query = intent.parameters.get("target", intent.original_text)
        return f"Explain: {query}"