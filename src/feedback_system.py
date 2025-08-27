"""User feedback system for voice commander with real-time display."""

import asyncio
import logging
import sys
import re
from typing import Optional
from .config import FeedbackConfig


class FeedbackSystem:
    """Provides audio and visual feedback to users with real-time text display."""
    
    def __init__(self, config: FeedbackConfig, terminal_controller=None):
        """Initialize feedback system."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.terminal_controller = terminal_controller
        
        # State
        self.tts_engine = None
        self.audio_enabled = config.enable_audio
        self.visual_enabled = config.enable_visual
        self.current_line = ""
        
        # Text concatenation state
        self.accumulated_text = ""
        self.is_accumulating = False
        self.finalization_keywords = ["send to claude", "execute command", "process request", "submit"]
    
    async def _output_feedback(self, message: str, local_only: bool = False):
        """Output feedback to appropriate destination."""
        # Don't output to local console anymore - remove visual clutter
        # Only log for debugging purposes
        self.logger.debug(f"Feedback: {message}")
        
        # Also send to target terminal if available and not local_only
        if not local_only and self.terminal_controller and hasattr(self.terminal_controller, 'send_feedback_message'):
            try:
                await self.terminal_controller.send_feedback_message(message)
            except Exception as e:
                self.logger.debug(f"Could not send to terminal: {e}")
    
    async def initialize(self):
        """Initialize feedback system components."""
        try:
            self.logger.info("Initializing feedback system...")
            
            if self.config.voice_feedback:
                # TODO: Initialize text-to-speech engine
                self.logger.info("Initializing text-to-speech...")
            
            # Don't show header anymore
            
            self.logger.info("Feedback system initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize feedback system: {e}")
            raise
    
    def _clear_screen(self):
        """Clear terminal screen."""
        print("\033[2J\033[H", end="")
    
    def _show_header(self):
        """Show application header."""
        print("=" * 60)
        print("🎤 Claude Voice Commander - Real-time Speech Recognition")
        print("=" * 60)
        print("Commands: 'plan mode', 'auto mode', 'option 1-5', 'yes/no'")
        print("-" * 60)
        print()
    
    async def play_ready_sound(self):
        """Play sound indicating system is ready."""
        # Don't show local visual feedback anymore
        self.logger.info("System ready! Start speaking...")
        
        if self.audio_enabled:
            # TODO: Play actual ready sound
            pass
    
    async def show_listening_indicator(self):
        """Show that system is listening."""
        # Don't show local visual feedback anymore
        self.logger.debug("Listening...")
        
        if self.audio_enabled:
            # TODO: Play listening sound/tone
            pass
    
    async def show_partial_text(self, text: str):
        """Show partial recognition text in real-time."""
        clean_text = text.strip()
        if not clean_text:
            return
            
        # Only log partial text, don't send to Claude terminal
        self.logger.debug(f"Partial text: {clean_text}")
        
        # Don't send partial text to Claude - wait for accumulation/finalization
    
    async def show_recognized_text(self, text: str):
        """Show final recognized speech text."""
        # Only log recognized text, don't send to Claude terminal
        self.logger.debug(f"Recognized: '{text}'")
        
        # Don't send recognized text to Claude - wait for accumulation/finalization
        
        if self.config.voice_feedback:
            await self._speak(f"I heard: {text}")
    
    async def show_text_accumulation_started(self, text: str):
        """Show that text accumulation has started."""
        self.logger.info(f"Started accumulating: {text}")
        
        # Send clean message to target terminal
        if self.terminal_controller and hasattr(self.terminal_controller, 'send_feedback_message'):
            try:
                await self.terminal_controller.send_feedback_message(f"[ACCUMULATING] {text}")
            except Exception as e:
                self.logger.debug(f"Could not send accumulation start to terminal: {e}")
    
    async def show_text_accumulated(self, new_text: str, full_text: str):
        """Show that additional text has been accumulated."""
        self.logger.info(f"Added: {new_text} | Full: {full_text}")
        
        # Send clean update to target terminal
        if self.terminal_controller and hasattr(self.terminal_controller, 'send_feedback_message'):
            try:
                await self.terminal_controller.send_feedback_message(f"[ADDED] {new_text}")
                await self.terminal_controller.send_feedback_message(f"[FULL TEXT] {full_text}")
            except Exception as e:
                self.logger.debug(f"Could not send accumulation update to terminal: {e}")
    
    async def show_finalization_ready(self, keywords: list):
        """Show available finalization keywords."""
        keywords_str = " / ".join([f'"{k}"' for k in keywords])
        self.logger.info(f"Ready to finalize. Say: {keywords_str}")
        
        # Send clean prompt to target terminal
        if self.terminal_controller and hasattr(self.terminal_controller, 'send_feedback_message'):
            try:
                await self.terminal_controller.send_feedback_message(f"[READY] Say {keywords_str} to execute")
            except Exception as e:
                self.logger.debug(f"Could not send finalization prompt to terminal: {e}")
    
    async def show_processing(self):
        """Show that command is being processed."""
        # Don't show local visual feedback anymore
        self.logger.debug("Processing command...")
        
        if self.config.voice_feedback:
            await self._speak("Processing your command")
    
    async def show_success(self, message: str = "Command completed successfully"):
        """Show successful command execution."""
        # Don't show local visual feedback anymore
        self.logger.info(f"Success: {message}")
        
        if self.config.voice_feedback:
            await self._speak("Command completed successfully")
        
        if self.audio_enabled:
            # TODO: Play success sound
            pass
    
    async def show_error(self, error_message: str):
        """Show error message."""
        # Don't show local visual feedback anymore
        self.logger.error(f"Error: {error_message}")
        
        if self.config.voice_feedback:
            await self._speak(f"Error: {error_message}")
        
        if self.audio_enabled:
            # TODO: Play error sound
            pass
    
    async def show_info(self, message: str):
        """Show informational message."""
        # Don't show local visual feedback anymore
        self.logger.info(f"Info: {message}")
        
        if self.config.voice_feedback:
            await self._speak(message)
    
    async def show_mode_switch(self, mode: str):
        """Show Claude mode switch."""
        # Don't show local visual feedback anymore
        self.logger.info(f"Switched to {mode.upper()} mode")
    
    async def show_selection(self, selection: str):
        """Show option selection."""
        # Don't show local visual feedback anymore
        self.logger.info(f"Selected: {selection}")
    
    async def show_confirmation(self, response: str):
        """Show confirmation response."""
        # Don't show local visual feedback anymore
        self.logger.info(f"Confirmation: {response.title()}")
    
    async def request_confirmation(self, command: str) -> bool:
        """Request user confirmation for command."""
        # Don't show local visual feedback anymore
        self.logger.info(f"Requesting confirmation for: {command}")
        
        if self.config.voice_feedback:
            await self._speak(f"Confirm command: {command}")
        
        # TODO: Implement actual confirmation input
        # For now, auto-confirm in development
        return True
    
    async def show_command_options(self, commands: list):
        """Show available command options."""
        # Don't show local visual feedback anymore
        self.logger.info(f"Available commands: {commands}")
    
    async def show_status(self, status: str, details: str = ""):
        """Show system status."""
        message = f"Status: {status}"
        if details:
            message += f" - {details}"
        
        # Don't show local visual feedback anymore
        self.logger.info(message)
        
        if self.config.voice_feedback:
            await self._speak(status)
    
    async def show_volume_level(self, level: float):
        """Show current microphone volume level."""
        # Don't show local visual feedback anymore
        if level > 0.1:
            self.logger.debug(f"Volume level: {level:.1%}")
    
    async def _speak(self, text: str):
        """Convert text to speech."""
        try:
            if not self.config.voice_feedback:
                return
            
            self.logger.debug(f"Speaking: '{text}'")
            
            # TODO: Implement actual text-to-speech
            # Placeholder: just log the speech
            await asyncio.sleep(0.1)  # Simulate speech time
            
        except Exception as e:
            self.logger.error(f"Error in text-to-speech: {e}")
    
    async def _play_sound(self, sound_type: str):
        """Play a system sound."""
        try:
            if not self.audio_enabled:
                return
            
            # TODO: Implement actual sound playback
            self.logger.debug(f"Playing sound: {sound_type}")
            
        except Exception as e:
            self.logger.error(f"Error playing sound: {e}")
    
    def _move_cursor_up(self, lines: int = 1):
        """Move cursor up N lines."""
        if self.visual_enabled:
            print(f"\033[{lines}A", end="")
    
    def _clear_current_line(self):
        """Clear current terminal line."""
        if self.visual_enabled:
            print("\r\033[K", end="", flush=True)
    
    async def cleanup(self):
        """Cleanup feedback system resources."""
        try:
            if self.tts_engine:
                # TODO: Cleanup TTS engine
                pass
            
            self.logger.info("Claude Voice Commander stopped")
            
            self.logger.info("Feedback system cleanup complete")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up feedback system: {e}")