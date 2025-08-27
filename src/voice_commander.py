"""Main Voice Commander orchestrator."""

import asyncio
import logging
from typing import Optional
from .config import Config
from .audio_capture import AudioCapture
from .speech_to_text import SpeechToTextService
from .command_processor import CommandProcessor
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
        self.command_processor = CommandProcessor()
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
        
        # Command Processing -> Terminal Controller
        self.command_processor.on_command_validated = self._handle_command_validated
        
        # Command Processing -> Feedback for text accumulation
        self.command_processor.on_text_accumulation_started = self._handle_accumulation_started
        self.command_processor.on_text_accumulated = self._handle_text_accumulated
        
        # Terminal Controller -> Feedback
        self.terminal_controller.on_action_completed = self._handle_action_completed
        self.terminal_controller.on_mode_switched = self._handle_mode_switched
        self.terminal_controller.on_selection_made = self._handle_selection_made
        self.terminal_controller.on_confirmation_sent = self._handle_confirmation_sent
        
        # Error handling
        for component in [self.audio_capture, self.speech_service, 
                         self.command_processor, self.terminal_controller]:
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
            
            # Process command
            await self.command_processor.process_text(text, confidence)
            
        except Exception as e:
            self.logger.error(f"Error processing recognized text: {e}")
            await self.feedback_system.show_error("Text processing failed")
    
    async def _handle_command_validated(self, command: str, intent: str, confidence: float):
        """Handle validated command."""
        try:
            self.logger.info(f"Validated command: '{command}' (intent: {intent})")
            
            # Show confirmation if required
            if self.config.feedback.confirmation_required:
                confirmed = await self.feedback_system.request_confirmation(command)
                if not confirmed:
                    await self.feedback_system.show_info("Command cancelled")
                    return
            
            await self.feedback_system.show_processing()
            
            # Send to Terminal Controller
            await self.terminal_controller.execute_command(command)
            
        except Exception as e:
            self.logger.error(f"Error processing command: {e}")
            await self.feedback_system.show_error("Command processing failed")
    
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
    
    async def _handle_mode_switched(self, mode: str):
        """Handle Claude mode switch."""
        try:
            await self.feedback_system.show_mode_switch(mode)
        except Exception as e:
            self.logger.error(f"Error handling mode switch: {e}")
    
    async def _handle_selection_made(self, selection: str):
        """Handle option selection."""
        try:
            await self.feedback_system.show_selection(f"option {selection}")
        except Exception as e:
            self.logger.error(f"Error handling selection: {e}")
    
    async def _handle_confirmation_sent(self, response: str):
        """Handle confirmation response."""
        try:
            await self.feedback_system.show_confirmation(response)
        except Exception as e:
            self.logger.error(f"Error handling confirmation: {e}")
    
    async def _handle_accumulation_started(self, text: str):
        """Handle text accumulation started."""
        try:
            await self.feedback_system.show_text_accumulation_started(text)
            await self.feedback_system.show_finalization_ready(self.command_processor.finalization_keywords)
        except Exception as e:
            self.logger.error(f"Error handling accumulation start: {e}")
    
    async def _handle_text_accumulated(self, new_text: str, full_text: str):
        """Handle additional text accumulated."""
        try:
            await self.feedback_system.show_text_accumulated(new_text, full_text)
        except Exception as e:
            self.logger.error(f"Error handling text accumulation: {e}")

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