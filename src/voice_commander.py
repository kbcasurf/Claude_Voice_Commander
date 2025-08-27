"""Main Voice Commander orchestrator."""

import asyncio
import logging
from typing import Optional
from .config import Config
from .audio_capture import AudioCapture
from .speech_to_text import SpeechToTextService
# Removed CommandProcessor - using simple text accumulation
from .universal_terminal_controller import UniversalTerminalController
from .feedback_system import FeedbackSystem


class VoiceCommander:
    """Main orchestrator for the voice command system."""
    
    def __init__(self, config: Config):
        """Initialize the voice commander with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.running = False
        
        # Initialize components
        self.audio_capture = AudioCapture(config.audio)
        self.speech_service = SpeechToTextService(config.whisper)
        # Simple text accumulation state
        self.accumulated_text = ""
        self.is_accumulating = False
        self.send_keywords = ["send this prompt", "send prompt"]
        self.editing_keywords = ["remove last word", "remove this line", "remove complete input", "start over"]
        self.selection_keywords = {
            "select option 1": "1",
            "select option 2": "2",
            "select option 3": "3",
            "select option 4": "4"
        }
        self.mode_keywords = ["change operation mode"]
        self.activation_keywords = ["activate voice commander", "start voice commander"]
        self.deactivation_keywords = ["stop voice commander", "deactivate voice commander"]
        self.listening_state = "SLEEPING"  # Start in safe mode
        self.confidence_threshold = 0.3
        # Use universal controller that works with any focused terminal
        self.terminal_controller = UniversalTerminalController(config.claude)
        self.feedback_system = FeedbackSystem(config.feedback, self.terminal_controller)
        
        # Event handling
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Set up event handlers between components."""
        # Audio -> Speech-to-Text
        self.audio_capture.on_audio_captured = self._handle_audio_captured
        
        # Speech-to-Text -> Command Processing
        self.speech_service.on_text_recognized = self._handle_text_recognized
        self.speech_service.on_partial_text = self._handle_partial_text
        
        # Removed command processor event handlers - using simple logic
        
        # Terminal Controller -> Feedback (simplified)
        self.terminal_controller.on_action_completed = self._handle_action_completed
        # Removed other handlers - no longer needed for simplified approach
        
        # Error handling
        for component in [self.audio_capture, self.speech_service, 
                         self.terminal_controller]:
            if hasattr(component, 'on_error'):
                component.on_error = self._handle_component_error
    
    async def start(self):
        """Start the voice commander system."""
        try:
            self.logger.info("Starting voice commander components...")
            self.running = True
            
            # Initialize all components
            await self._initialize_components()
            
            # Start audio capture
            await self.audio_capture.start()
            
            self.logger.info("Voice Commander is ready! Speak your commands...")
            await self.feedback_system.play_ready_sound()
            
            # Main event loop
            await self._main_loop()
            
        except Exception as e:
            self.logger.error(f"Error starting voice commander: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the voice commander system."""
        self.logger.info("Stopping voice commander...")
        self.running = False
        
        # Stop all components
        if hasattr(self, 'audio_capture'):
            await self.audio_capture.stop()
        
        # Cleanup
        await self._cleanup_components()
        
        self.logger.info("Voice commander stopped")
    
    async def _initialize_components(self):
        """Initialize all components."""
        components = [
            ("Speech Service", self.speech_service),
            ("Terminal Controller", self.terminal_controller),
            ("Feedback System", self.feedback_system)
        ]
        
        for name, component in components:
            try:
                if hasattr(component, 'initialize'):
                    await component.initialize()
                    self.logger.debug(f"Initialized {name}")
            except Exception as e:
                self.logger.error(f"Failed to initialize {name}: {e}")
                raise
    
    async def _cleanup_components(self):
        """Cleanup all components."""
        components = [self.feedback_system, self.terminal_controller, 
                     self.speech_service, self.audio_capture]
        
        for component in components:
            try:
                if hasattr(component, 'cleanup'):
                    await component.cleanup()
            except Exception as e:
                self.logger.warning(f"Error cleaning up component: {e}")
    
    async def _main_loop(self):
        """Main event processing loop."""
        while self.running:
            try:
                # Process any pending events
                await asyncio.sleep(0.1)
                
            except KeyboardInterrupt:
                self.logger.info("Received interrupt signal")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                if self.config.debug_mode:
                    raise
    
    async def _handle_audio_captured(self, audio_data: bytes):
        """Handle captured audio data."""
        try:
            self.logger.debug("Audio captured, processing...")
            await self.feedback_system.show_listening_indicator()
            
            # Send to speech recognition
            await self.speech_service.process_audio(audio_data)
            
        except Exception as e:
            self.logger.error(f"Error processing audio: {e}")
            await self.feedback_system.show_error("Audio processing failed")
    
    async def _handle_partial_text(self, text: str):
        """Handle partial text for real-time display."""
        try:
            await self.feedback_system.show_partial_text(text)
        except Exception as e:
            self.logger.error(f"Error showing partial text: {e}")
    
    async def _handle_text_recognized(self, text: str, confidence: float):
        """Handle recognized speech text."""
        try:
            self.logger.info(f"Recognized: '{text}' (confidence: {confidence:.2f})")
            await self.feedback_system.show_recognized_text(text)
            
            # Simple text processing
            await self._process_simple_text(text, confidence)
            
        except Exception as e:
            self.logger.error(f"Error processing recognized text: {e}")
            await self.feedback_system.show_error("Text processing failed")
    
    async def _process_simple_text(self, text: str, confidence: float):
        """Simple text processing with voice activation control."""
        try:
            # Check confidence threshold
            if confidence < self.confidence_threshold:
                self.logger.warning(f"Low confidence recognition: {confidence}")
                return
            
            # Normalize text
            normalized_text = text.lower().strip()
            
            # Handle activation/deactivation regardless of current state
            if any(keyword in normalized_text for keyword in self.activation_keywords):
                if self.listening_state == "SLEEPING":
                    self.listening_state = "ACTIVE"
                    self.logger.info("Voice Commander ACTIVATED - Now listening for all commands")
                    await self.feedback_system.show_success("Voice Commander activated")
                return
            
            if any(keyword in normalized_text for keyword in self.deactivation_keywords):
                if self.listening_state == "ACTIVE":
                    self.listening_state = "SLEEPING"
                    # Clear any accumulated text when deactivating
                    self.accumulated_text = ""
                    self.is_accumulating = False
                    self.logger.info("Voice Commander DEACTIVATED - Only listening for activation keywords")
                    await self.feedback_system.show_success("Voice Commander deactivated")
                return
            
            # If sleeping, ignore all other commands
            if self.listening_state == "SLEEPING":
                self.logger.debug(f"Ignoring text while sleeping: '{text}'")
                return
            
            # Continue with normal processing only if ACTIVE
            
            # Check for send keywords (acts like Enter key)
            if any(keyword in normalized_text for keyword in self.send_keywords):
                # Just press Enter - text is already typed in Claude terminal
                self.logger.info("Pressing Enter key")
                await self.terminal_controller._send_key_to_window("Return")
                
                # Reset accumulation state for next command
                self.accumulated_text = ""
                self.is_accumulating = False
                
                await self.feedback_system.show_success("Sent (Enter pressed)")
                return
            
            # Check for editing commands (act like keyboard shortcuts)
            if any(keyword in normalized_text for keyword in self.editing_keywords):
                if "remove last word" in normalized_text:
                    # Send Alt+Backspace to remove last word in terminal
                    self.logger.info("Removing last word (Alt+Backspace)")
                    await self.terminal_controller._send_key_to_window("alt+BackSpace")
                    
                    # Update internal state
                    if self.accumulated_text:
                        words = self.accumulated_text.split()
                        if words:
                            words.pop()
                            self.accumulated_text = " ".join(words)
                    
                    await self.feedback_system.show_success("Removed last word")
                
                elif "remove this line" in normalized_text or "remove complete input" in normalized_text:
                    # Send Ctrl+U to clear current line in terminal
                    self.logger.info("Clearing line (Ctrl+U)")
                    await self.terminal_controller._send_key_to_window("ctrl+u")
                    
                    # Reset internal state
                    self.accumulated_text = ""
                    self.is_accumulating = False
                    
                    await self.feedback_system.show_success("Cleared line")
                
                elif "start over" in normalized_text:
                    # Send Ctrl+A then Delete to clear everything
                    self.logger.info("Clearing all (Ctrl+A, Delete)")
                    await self.terminal_controller._send_key_to_window("ctrl+a")
                    await asyncio.sleep(0.1)
                    await self.terminal_controller._send_key_to_window("Delete")
                    
                    # Reset internal state
                    self.accumulated_text = ""
                    self.is_accumulating = False
                    
                    await self.feedback_system.show_success("Started over")
                
                return
            
            # Check for option selection commands
            for phrase, number in self.selection_keywords.items():
                if phrase in normalized_text:
                    # Send number key for option selection
                    self.logger.info(f"Selecting option {number}")
                    await self.terminal_controller._send_key_to_window(number)
                    await self.feedback_system.show_success(f"Selected option {number}")
                    return
            
            # Check for mode change command
            if any(keyword in normalized_text for keyword in self.mode_keywords):
                # Send Shift+Tab to change operation mode
                self.logger.info("Changing operation mode (Shift+Tab)")
                await self.terminal_controller._send_key_to_window("shift+Tab")
                await self.feedback_system.show_success("Changed operation mode")
                return
            
            # Type text directly into Claude terminal (like a keyboard)
            if not self.is_accumulating:
                # Start typing - send text immediately to Claude
                self.is_accumulating = True
                self.accumulated_text = text
                self.logger.info(f"Typing: '{text}'")
                await self.terminal_controller._send_to_window(text)
                await self.feedback_system.show_text_accumulation_started(text)
            else:
                # Continue typing - add space and new text
                self.accumulated_text += " " + text
                self.logger.info(f"Typing more: '{text}' -> Full: '{self.accumulated_text}'")
                await self.terminal_controller._send_to_window(" " + text)
                await self.feedback_system.show_text_accumulated(text, self.accumulated_text)
                
        except Exception as e:
            self.logger.error(f"Error in simple text processing: {e}")
    
    # Removed _handle_command_validated - no longer needed
    
    async def _handle_action_completed(self, action: str, success: bool, details: str = ""):
        """Handle terminal action completion."""
        try:
            if success:
                self.logger.info(f"Action completed: {action}")
                await self.feedback_system.show_success(f"{action} completed")
            else:
                self.logger.warning(f"Action failed: {action} - {details}")
                await self.feedback_system.show_error(f"{action} failed: {details}")
                
        except Exception as e:
            self.logger.error(f"Error handling action completion: {e}")
    
    # Removed old handler methods - no longer needed for simplified approach

    async def _handle_component_error(self, component_name: str, error: Exception):
        """Handle errors from components."""
        self.logger.error(f"Error in {component_name}: {error}")
        await self.feedback_system.show_error(f"{component_name} error")
        
        # Attempt recovery for critical components
        if component_name == "AudioCapture" and self.running:
            self.logger.info("Attempting to restart audio capture...")
            try:
                await self.audio_capture.restart()
            except Exception as restart_error:
                self.logger.error(f"Failed to restart audio capture: {restart_error}")
                self.running = False