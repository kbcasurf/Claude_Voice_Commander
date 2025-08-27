"""Real-time speech-to-text service using local Whisper."""

import asyncio
import logging
import numpy as np
import threading
import queue
import time
import io
from typing import Optional, Callable, List
from .config import WhisperConfig


class SpeechToTextService:
    """Handles real-time speech-to-text conversion using local Whisper."""
    
    def __init__(self, config: WhisperConfig):
        """Initialize speech-to-text service."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Event handlers
        self.on_text_recognized: Optional[Callable[[str, float], None]] = None
        self.on_partial_text: Optional[Callable[[str], None]] = None  # For real-time display
        self.on_error: Optional[Callable[[str, Exception], None]] = None
        
        # Whisper model
        self.model = None
        self.vad = None  # Voice Activity Detection
        
        # Real-time processing
        self.audio_queue = queue.Queue()
        self.processing_thread = None
        self.stop_event = threading.Event()
        self.is_running = False
        
        # Audio buffering for streaming
        self.audio_buffer = []
        self.buffer_duration = 0.0
        self.sample_rate = 16000  # Whisper expects 16kHz
    
    async def initialize(self):
        """Initialize the speech-to-text service."""
        try:
            self.logger.info("Initializing real-time speech-to-text service...")
            
            # Load faster-whisper model
            try:
                from faster_whisper import WhisperModel
                
                self.logger.info(f"Loading Whisper model: {self.config.model_size}")
                self.model = WhisperModel(
                    self.config.model_size,
                    device=self.config.device,
                    compute_type=self.config.compute_type
                )
                self.logger.info("Whisper model loaded successfully")
                
            except ImportError:
                self.logger.error("faster-whisper not installed. Please install: pip install faster-whisper")
                raise
            except Exception as e:
                self.logger.error(f"Failed to load Whisper model: {e}")
                raise
            
            # Initialize Voice Activity Detection (optional)
            if self.config.vad_filter:
                try:
                    import webrtcvad
                    self.vad = webrtcvad.Vad(3)  # Aggressiveness level 0-3
                    self.logger.info("Voice Activity Detection enabled")
                except ImportError:
                    self.logger.warning("webrtcvad not available, VAD disabled")
                    self.config.vad_filter = False
            
            # Start processing thread
            self.stop_event.clear()
            self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
            self.processing_thread.start()
            self.is_running = True
            
            self.logger.info("Real-time speech-to-text service initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize speech service: {e}")
            raise
    
    async def process_audio(self, audio_data: bytes):
        """Process audio data and add to processing queue."""
        try:
            if not self.is_running:
                return
            
            # Convert audio data to numpy array and resample if needed
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Put audio in processing queue for real-time processing
            try:
                self.audio_queue.put_nowait(audio_array)
            except queue.Full:
                self.logger.warning("Audio queue full, dropping audio chunk")
                
        except Exception as e:
            self.logger.error(f"Error queuing audio: {e}")
            if self.on_error:
                await self.on_error("SpeechToText", e)
    
    def _processing_loop(self):
        """Main processing loop for real-time speech recognition."""
        self.logger.debug("Speech processing loop started")
        
        while not self.stop_event.is_set():
            try:
                # Get audio from queue with timeout
                try:
                    audio_chunk = self.audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # Add to buffer
                self.audio_buffer.extend(audio_chunk)
                chunk_duration = len(audio_chunk) / self.sample_rate
                self.buffer_duration += chunk_duration
                
                # Process when we have enough audio
                if self.buffer_duration >= self.config.chunk_length:
                    self._process_buffer()
                
            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}")
        
        self.logger.debug("Speech processing loop stopped")
    
    def _process_buffer(self):
        """Process accumulated audio buffer."""
        try:
            if not self.audio_buffer:
                return
            
            # Convert to numpy array
            audio_array = np.array(self.audio_buffer, dtype=np.float32)
            
            # Voice Activity Detection
            if self.config.vad_filter and self.vad:
                if not self._has_speech(audio_array):
                    self._reset_buffer()
                    return
            
            # Resample to 16kHz if needed
            if len(audio_array) > 0:
                audio_16k = self._resample_audio(audio_array)
                
                # Transcribe with Whisper
                text, confidence = self._transcribe_audio(audio_16k)
                
                if text.strip():
                    # Send partial text for real-time display
                    if self.on_partial_text:
                        self._trigger_callback(self.on_partial_text, text)
                    
                    # Send final recognition
                    if confidence > 0.3:  # Confidence threshold
                        self._trigger_callback(self.on_text_recognized, text, confidence)
            
            # Reset buffer with overlap
            overlap_samples = int(self.config.overlap_length * self.sample_rate)
            if len(self.audio_buffer) > overlap_samples:
                self.audio_buffer = self.audio_buffer[-overlap_samples:]
                self.buffer_duration = self.config.overlap_length
            else:
                self._reset_buffer()
                
        except Exception as e:
            self.logger.error(f"Error processing audio buffer: {e}")
            self._reset_buffer()
    
    def _transcribe_audio(self, audio: np.ndarray) -> tuple[str, float]:
        """Transcribe audio using local Whisper model."""
        try:
            if self.model is None:
                return "", 0.0
            
            # Run transcription
            segments, info = self.model.transcribe(
                audio,
                language=self.config.language,
                beam_size=self.config.beam_size,
                temperature=self.config.temperature,
                vad_filter=False,  # We handle VAD ourselves
                word_timestamps=True
            )
            
            # Combine segments
            text_parts = []
            total_confidence = 0.0
            segment_count = 0
            
            for segment in segments:
                text_parts.append(segment.text.strip())
                total_confidence += getattr(segment, 'avg_logprob', -1.0)
                segment_count += 1
            
            text = " ".join(text_parts).strip()
            confidence = max(0.0, (total_confidence / segment_count + 1.0)) if segment_count > 0 else 0.0
            
            self.logger.debug(f"Transcribed: '{text}' (confidence: {confidence:.3f})")
            return text, confidence
            
        except Exception as e:
            self.logger.error(f"Error transcribing audio: {e}")
            return "", 0.0
    
    def _has_speech(self, audio: np.ndarray) -> bool:
        """Check if audio contains speech using VAD."""
        if not self.vad:
            return True
        
        try:
            # Convert to 16-bit PCM
            audio_16bit = (audio * 32767).astype(np.int16).tobytes()
            
            # VAD requires specific frame sizes (10, 20, or 30ms)
            frame_duration = 30  # ms
            frame_size = int(self.sample_rate * frame_duration / 1000)
            
            # Check frames for speech
            speech_frames = 0
            total_frames = 0
            
            for i in range(0, len(audio_16bit) - frame_size * 2, frame_size * 2):
                frame = audio_16bit[i:i + frame_size * 2]
                if len(frame) == frame_size * 2:  # Ensure full frame
                    if self.vad.is_speech(frame, self.sample_rate):
                        speech_frames += 1
                    total_frames += 1
            
            if total_frames == 0:
                return False
            
            speech_ratio = speech_frames / total_frames
            return speech_ratio > 0.3  # 30% of frames contain speech
            
        except Exception as e:
            self.logger.debug(f"VAD error: {e}")
            return True  # Assume speech if VAD fails
    
    def _resample_audio(self, audio: np.ndarray) -> np.ndarray:
        """Resample audio to 16kHz for Whisper."""
        # For now, assume input is already 16kHz (will be handled by audio capture)
        return audio
    
    def _reset_buffer(self):
        """Reset audio buffer."""
        self.audio_buffer = []
        self.buffer_duration = 0.0
    
    def _trigger_callback(self, callback, *args):
        """Trigger async callback from sync context."""
        if callback:
            try:
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(callback(*args))
                loop.close()
            except Exception as e:
                self.logger.error(f"Error triggering callback: {e}")
    
    async def cleanup(self):
        """Cleanup speech-to-text resources."""
        self.logger.info("Cleaning up speech-to-text service...")
        
        self.is_running = False
        self.stop_event.set()
        
        # Wait for processing thread
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)
        
        # Clear queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
        
        self.model = None
        self.vad = None
        
        self.logger.info("Speech-to-text service cleanup complete")