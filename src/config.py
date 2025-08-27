"""Configuration management for Claude Voice Commander."""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class AudioConfig:
    """Audio capture configuration."""
    sample_rate: int = 16000  # Whisper expects 16kHz
    channels: int = 1
    chunk_size: int = 1024
    device_index: Optional[int] = None
    silence_threshold: float = 0.01
    silence_duration: float = 1.5  # seconds - longer for better phrase detection


@dataclass
class WhisperConfig:
    """Whisper speech-to-text configuration."""
    model_size: str = "tiny"  # tiny is fastest for CPU, still very accurate
    device: str = "cpu"  # cpu only
    compute_type: str = "int8"  # int8 is fastest for CPU
    language: Optional[str] = "en"  # English for faster processing
    beam_size: int = 1  # Fastest beam size
    temperature: float = 0.0
    vad_filter: bool = True  # Voice activity detection
    chunk_length: int = 1  # shorter chunks for faster real-time response
    overlap_length: float = 0.2  # shorter overlap for speed


@dataclass
class ClaudeConfig:
    """Claude Code CLI configuration."""
    sdk_enabled: bool = True
    cli_path: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3


@dataclass 
class FeedbackConfig:
    """User feedback configuration."""
    enable_audio: bool = True
    enable_visual: bool = True
    voice_feedback: bool = False
    confirmation_required: bool = False


@dataclass
class Config:
    """Main configuration class for Claude Voice Commander."""
    
    # Core configurations
    audio: AudioConfig = field(default_factory=AudioConfig)
    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    claude: ClaudeConfig = field(default_factory=ClaudeConfig)
    feedback: FeedbackConfig = field(default_factory=FeedbackConfig)
    
    # General settings
    log_level: str = "INFO"
    config_file: str = "voice_commander.config"
    debug_mode: bool = False
    
    def __post_init__(self):
        """Initialize configuration from environment variables and config file."""
        self._load_from_env()
        self._load_from_file()
        self._validate_config()
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        # Whisper configuration
        if model_size := os.getenv("WHISPER_MODEL_SIZE"):
            self.whisper.model_size = model_size
            
        if device := os.getenv("WHISPER_DEVICE"):
            self.whisper.device = device
            
        if compute_type := os.getenv("WHISPER_COMPUTE_TYPE"):
            self.whisper.compute_type = compute_type
            
        # Claude configuration
        if claude_path := os.getenv("CLAUDE_CLI_PATH"):
            self.claude.cli_path = claude_path
            
        # General settings
        if log_level := os.getenv("LOG_LEVEL"):
            self.log_level = log_level.upper()
            
        if os.getenv("DEBUG_MODE", "").lower() == "true":
            self.debug_mode = True
    
    def _load_from_file(self):
        """Load configuration from config file if it exists."""
        config_path = Path(self.config_file)
        if config_path.exists():
            # TODO: Implement config file loading (JSON/YAML)
            pass
    
    def _validate_config(self):
        """Validate configuration settings."""
        # Validate Whisper model size
        valid_models = ["tiny", "base", "small", "medium", "large-v2", "large-v3"]
        if self.whisper.model_size not in valid_models:
            raise ValueError(f"Invalid Whisper model size: {self.whisper.model_size}. Valid options: {valid_models}")
            
        # Validate device
        valid_devices = ["cpu", "cuda", "auto"]
        if self.whisper.device not in valid_devices:
            raise ValueError(f"Invalid device: {self.whisper.device}. Valid options: {valid_devices}")
            
        if self.debug_mode:
            self.log_level = "DEBUG"
    
    def get_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary for debugging."""
        return {
            "audio": self.audio.__dict__,
            "whisper": self.whisper.__dict__,
            "claude": self.claude.__dict__,
            "feedback": self.feedback.__dict__,
            "log_level": self.log_level,
            "debug_mode": self.debug_mode,
        }