"""Universal terminal controller that works with any focused terminal."""

import asyncio
import logging
import subprocess
import time
from typing import Optional, Callable, Dict, List

from .config import ClaudeConfig


class UniversalTerminalController:
    """Controls any terminal window through focus-based xdotool automation."""
    
    def __init__(self, config: ClaudeConfig):
        """Initialize universal terminal controller."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Event handlers
        self.on_action_completed: Optional[Callable[[str, bool, str], None]] = None
        self.on_mode_switched: Optional[Callable[[str], None]] = None
        self.on_selection_made: Optional[Callable[[str], None]] = None
        self.on_confirmation_sent: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str, Exception], None]] = None
        
        # Window state
        self.target_window_id = None
        self.current_mode = "interactive"
        self.is_target_set = False
        self.focus_countdown = 10  # seconds to focus on target window
        
        # Command mappings for voice control
        self.mode_commands = {
            "plan mode": "/plan",
            "planning mode": "/plan", 
            "auto mode": "/auto",
            "automatic mode": "/auto",
            "auto accept": "/auto",
            "interactive mode": "/interactive",
            "ask mode": "/interactive",
            "ask before apply": "/interactive"
        }
        
        self.shortcuts = {
            "option one": "1",
            "option two": "2", 
            "option three": "3",
            "option four": "4",
            "option five": "5",
            "select one": "1",
            "select two": "2",
            "select three": "3", 
            "select four": "4",
            "select five": "5",
            "yes": "y",
            "no": "n",
            "accept": "y",
            "reject": "n",
            "continue": "y",
            "cancel": "n",
            "quit": "q",
            "exit": "q",
            "help": "h"
        }
    
    async def initialize(self):
        """Initialize universal terminal controller with focus capture."""
        try:
            self.logger.info("Initializing universal terminal controller...")
            
            # Check if xdotool is available
            if not await self._check_xdotool_available():
                raise RuntimeError("xdotool not found or not working")
            
            # Start focus capture process
            await self._capture_target_window()
            
            self.logger.info("Universal terminal controller initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize universal controller: {e}")
            raise
    
    async def _check_xdotool_available(self) -> bool:
        """Check if xdotool is available and working."""
        try:
            process = await asyncio.create_subprocess_exec(
                'xdotool', 'getwindowfocus',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5)
            
            if process.returncode == 0:
                focused_window = stdout.decode('utf-8').strip()
                self.logger.info(f"xdotool working, focused window: {focused_window}")
                return True
            else:
                self.logger.error(f"xdotool test failed: {stderr.decode('utf-8')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Cannot test xdotool: {e}")
            return False
    
    async def _capture_target_window(self):
        """Capture the target window with countdown."""
        try:
            print("\n" + "="*60)
            print("🎯 CLAUDE VOICE COMMANDER - TARGET WINDOW SETUP")
            print("="*60)
            print("You have 10 seconds to focus on the terminal where you want")
            print("to run Claude commands. This can be ANY terminal in ANY project.")
            print("")
            print("Instructions:")
            print("1. Click on the terminal where Claude is running")
            print("2. Make sure that terminal is focused/active")
            print("3. Wait for the countdown to finish")
            print("")
            
            # Countdown
            for i in range(self.focus_countdown, 0, -1):
                print(f"⏰ Focus on your target terminal now... {i} seconds remaining", end='\r')
                await asyncio.sleep(1)
            
            print("\n🎯 Capturing focused window...                              ")
            
            # Get the currently focused window
            process = await asyncio.create_subprocess_exec(
                'xdotool', 'getwindowfocus',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=3)
            
            if process.returncode == 0:
                self.target_window_id = stdout.decode('utf-8').strip()
                
                # Get window details
                window_name = await self._get_window_name(self.target_window_id)
                window_class = await self._get_window_class(self.target_window_id)
                
                print(f"✅ Target window captured!")
                print(f"   Window ID: {self.target_window_id}")
                print(f"   Window Name: '{window_name}'")
                print(f"   Window Class: '{window_class}'")
                print("")
                
                # Test the window
                print("🧪 Testing window control...")
                await self._send_to_window("# Voice Commander Connected - Test Message")
                await asyncio.sleep(0.5)
                await self._send_key_to_window("Return")
                
                print("✅ Test message sent!")
                print("   Check your terminal - you should see the test message")
                print("")
                
                self.is_target_set = True
                
                print("🎉 Voice Commander is ready!")
                print("   All voice commands will be sent to the captured window")
                print("="*60)
                
            else:
                raise RuntimeError(f"Failed to get focused window: {stderr.decode('utf-8')}")
                
        except Exception as e:
            self.logger.error(f"Error capturing target window: {e}")
            raise
    
    async def _get_window_name(self, window_id: str) -> str:
        """Get window name safely."""
        try:
            process = await asyncio.create_subprocess_exec(
                'xdotool', 'getwindowname', window_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=1)
            
            if process.returncode == 0:
                return stdout.decode('utf-8').strip()
            return "Unknown"
            
        except Exception:
            return "Unknown"
    
    async def _get_window_class(self, window_id: str) -> str:
        """Get window class safely."""
        try:
            process = await asyncio.create_subprocess_exec(
                'xdotool', 'getwindowclassname', window_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=1)
            
            if process.returncode == 0:
                return stdout.decode('utf-8').strip()
            return "Unknown"
            
        except Exception:
            return "Unknown"
    
    async def execute_command(self, command: str):
        """Execute a command in the target terminal."""
        try:
            self.logger.info(f"Executing command: '{command}'")
            
            # Check for special voice commands first
            if await self._handle_special_commands(command):
                return
            
            # Ensure we have a target window
            if not self.is_target_set:
                self.logger.error("No target window set")
                if self.on_action_completed:
                    await self.on_action_completed("no_target", False, "No target window configured")
                return
            
            # Send command to target window
            await self._send_to_window(command)
            await self._send_key_to_window("Return")
            
            if self.on_action_completed:
                await self.on_action_completed("command", True, f"Sent: {command}")
                
        except Exception as e:
            self.logger.error(f"Error executing command: {e}")
            if self.on_error:
                await self.on_error("UniversalTerminalController", e)
    
    async def _handle_special_commands(self, command: str) -> bool:
        """Handle special voice commands for Claude CLI control."""
        command_lower = command.lower().strip()
        
        # Check for mode switching commands
        for voice_cmd, cli_cmd in self.mode_commands.items():
            if voice_cmd in command_lower:
                await self._send_to_window(cli_cmd)
                await self._send_key_to_window("Return")
                self.current_mode = cli_cmd[1:]  # Remove the '/'
                self.logger.info(f"Switched to {self.current_mode} mode")
                if self.on_mode_switched:
                    await self.on_mode_switched(self.current_mode)
                if self.on_action_completed:
                    await self.on_action_completed("mode_switch", True, f"Switched to {self.current_mode} mode")
                return True
        
        # Check for shortcut commands  
        for voice_cmd, key in self.shortcuts.items():
            if command_lower == voice_cmd or command_lower.endswith(voice_cmd):
                await self._send_key_to_window(key)
                self.logger.info(f"Sent shortcut: {voice_cmd} -> {key}")
                
                # Trigger specific callbacks for different types
                if voice_cmd.startswith(("option", "select")):
                    if self.on_selection_made:
                        await self.on_selection_made(key)
                elif voice_cmd in ["yes", "no", "accept", "reject", "continue", "cancel"]:
                    if self.on_confirmation_sent:
                        await self.on_confirmation_sent(voice_cmd)
                        
                if self.on_action_completed:
                    await self.on_action_completed("shortcut", True, f"Sent: {key}")
                return True
        
        # Check for number selection (fallback)
        if command_lower.startswith("select ") or command_lower.startswith("option "):
            try:
                words = command_lower.split()
                for word in words:
                    if word.isdigit():
                        await self._send_key_to_window(word)
                        self.logger.info(f"Sent number: {word}")
                        if self.on_action_completed:
                            await self.on_action_completed("selection", True, f"Selected: {word}")
                        return True
            except:
                pass
        
        return False
    
    async def _send_to_window(self, text: str):
        """Send text to the target window using xdotool."""
        if not self.target_window_id:
            raise RuntimeError("No target window set")
        
        try:
            # Activate the window first
            await self._run_xdotool(['windowactivate', self.target_window_id])
            await asyncio.sleep(0.1)
            
            # Send the text
            await self._run_xdotool(['type', '--delay', '50', text])
            
            self.logger.debug(f"Sent to window {self.target_window_id}: {text[:50]}...")
            
        except Exception as e:
            self.logger.error(f"Error sending to window: {e}")
            raise
    
    async def _send_key_to_window(self, key: str):
        """Send a single key to the target window."""
        if not self.target_window_id:
            raise RuntimeError("No target window set")
        
        try:
            # Activate the window
            await self._run_xdotool(['windowactivate', self.target_window_id])
            await asyncio.sleep(0.05)
            
            # Send the key
            await self._run_xdotool(['key', key])
            
            self.logger.debug(f"Sent key to window {self.target_window_id}: {key}")
            
        except Exception as e:
            self.logger.error(f"Error sending key to window: {e}")
            raise
    
    async def _run_xdotool(self, args: List[str]):
        """Run xdotool command asynchronously."""
        try:
            process = await asyncio.create_subprocess_exec(
                'xdotool', *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5)
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8').strip()
                raise RuntimeError(f"xdotool failed: {error_msg}")
                
            return stdout.decode('utf-8').strip()
            
        except Exception as e:
            self.logger.error(f"xdotool command failed: {' '.join(args)} - {e}")
            raise
    
    async def switch_mode(self, mode: str):
        """Switch Claude CLI mode."""
        mode_mapping = {
            "plan": "/plan",
            "auto": "/auto", 
            "interactive": "/interactive"
        }
        
        if mode in mode_mapping:
            await self._send_to_window(mode_mapping[mode])
            await self._send_key_to_window("Return")
            self.current_mode = mode
            self.logger.info(f"Switched to {mode} mode")
        else:
            self.logger.warning(f"Unknown mode: {mode}")
    
    async def send_feedback_message(self, message: str, newline: bool = True):
        """Send a feedback message to the target terminal."""
        try:
            if not self.is_target_set:
                return
            
            # Send message directly without hashtag prefix
            await self._send_to_window(message)
            if newline:
                await self._send_key_to_window("Return")
            
            self.logger.debug(f"Sent feedback to target terminal: {message}")
            
        except Exception as e:
            self.logger.error(f"Error sending feedback message: {e}")
    
    async def recapture_window(self):
        """Recapture the target window."""
        self.is_target_set = False
        self.target_window_id = None
        await self._capture_target_window()
    
    async def cleanup(self):
        """Cleanup universal terminal controller resources."""
        try:
            self.logger.info("Universal terminal controller cleanup complete")
        except Exception as e:
            self.logger.error(f"Error cleaning up universal controller: {e}")
    
    def is_claude_active(self) -> bool:
        """Check if target window is set."""
        return self.is_target_set and self.target_window_id is not None