"""Audio capture module for real-time microphone input using PulseAudio."""

import asyncio
import logging
import numpy as np
import threading
import subprocess
import time
from typing import Optional, Callable, List
from .config import AudioConfig


class AudioCapture:
    """Handles real-time audio capture from microphone."""
    
    def __init__(self, config: AudioConfig):
        """Initialize audio capture with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.stream = None
        self.pyaudio = None
        
        # Event handlers
        self.on_audio_captured: Optional[Callable[[bytes], None]] = None
        self.on_error: Optional[Callable[[str, Exception], None]] = None
        
        # Audio processing
        self.audio_buffer: List[bytes] = []
        self.silence_counter = 0
        self.recording = False
        self.min_recording_length = 0.5  # Minimum recording length in seconds
        self.max_recording_length = 10.0  # Maximum recording length in seconds
        
        # Threading
        self.capture_thread = None
        self.processing_thread = None
        self.stop_event = threading.Event()
    
    async def start(self):
        """Start audio capture using PulseAudio."""
        try:
            self.logger.info("Starting audio capture with PulseAudio...")
            
            # Start PulseAudio recording process
            cmd = [
                'parec',
                '--format=s16le',
                f'--rate={self.config.sample_rate}',
                '--channels=1',  # Mono for speech recognition
                '--latency=100'
            ]
            
            self.stream = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )
            
            self.is_running = True
            self.stop_event.clear()
            
            # Start capture thread
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            self.logger.info("PulseAudio capture started successfully (using default Fifine mic)")
            
        except Exception as e:
            self.logger.error(f"Failed to start audio capture: {e}")
            if self.on_error:
                await self.on_error("AudioCapture", e)
            raise
    
    async def stop(self):
        """Stop audio capture."""
        try:
            self.logger.info("Stopping audio capture...")
            self.is_running = False
            self.stop_event.set()
            
            # Stop PulseAudio process
            if self.stream:
                self.stream.terminate()
                self.stream = None
            
            # Wait for processing thread to finish
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=2.0)
            
            self.logger.info("Audio capture stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping audio capture: {e}")
    
    async def restart(self):
        """Restart audio capture."""
        await self.stop()
        await asyncio.sleep(1)  # Brief pause
        await self.start()
    
    def _capture_loop(self):
        """Main capture loop for PulseAudio."""
        self.logger.debug("Audio capture loop started")
        
        chunk_size = self.config.chunk_size * 2  # *2 for 16-bit samples
        
        while self.is_running and self.stream:
            try:
                # Read audio from PulseAudio
                raw_audio = self.stream.stdout.read(chunk_size)
                
                if len(raw_audio) > 0:
                    # Convert to numpy array
                    audio_array = np.frombuffer(raw_audio, dtype=np.int16)
                    
                    # Calculate RMS for volume detection
                    rms = np.sqrt(np.mean(audio_array.astype(np.float32)**2)) / 32768.0
                    
                    # Check if audio contains speech
                    is_speech = rms > self.config.silence_threshold
                    
                    if is_speech:
                        if not self.recording:
                            self.logger.debug("Speech detected - starting recording")
                            self.recording = True
                            self.silence_counter = 0
                            self.audio_buffer = []
                        
                        self.audio_buffer.append(raw_audio)
                        self.silence_counter = 0
                    else:
                        if self.recording:
                            self.silence_counter += 1
                            self.audio_buffer.append(raw_audio)
                            
                            # Check if we should stop recording
                            silence_duration = self.silence_counter * self.config.chunk_size / self.config.sample_rate
                            recording_duration = len(self.audio_buffer) * self.config.chunk_size / self.config.sample_rate
                            
                            if (silence_duration > self.config.silence_duration and 
                                recording_duration > self.min_recording_length) or \
                               recording_duration > self.max_recording_length:
                                
                                self.logger.debug(f"Recording complete - duration: {recording_duration:.2f}s")
                                self.recording = False
                                
                                # Trigger processing
                                self._trigger_audio_processing()
                
            except Exception as e:
                if self.is_running:
                    self.logger.error(f"Error in capture loop: {e}")
                break
        
        self.logger.debug("Audio capture loop stopped")
    
    def _trigger_audio_processing(self):
        """Trigger audio processing in async context."""
        if self.audio_buffer and self.on_audio_captured:
            audio_data = b''.join(self.audio_buffer)
            self.audio_buffer = []
            
            # Create a new event loop for this thread if needed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Schedule the async callback
            if loop.is_running():
                asyncio.create_task(self.on_audio_captured(audio_data))
            else:
                loop.run_until_complete(self.on_audio_captured(audio_data))
    
    def _processing_loop(self):
        """Processing loop running in separate thread."""
        self.logger.debug("Audio processing loop started")
        
        while not self.stop_event.wait(0.1):  # Check every 100ms
            try:
                # Any additional processing can be done here
                pass
            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}")
        
        self.logger.debug("Audio processing loop stopped")
    
    def _process_audio_chunk(self, audio_chunk: bytes) -> bool:
        """Process an audio chunk and detect speech/silence."""
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_chunk, dtype=np.int16)
            
            # Calculate RMS for volume detection
            rms = np.sqrt(np.mean(audio_array**2))
            
            # Normalize to 0-1 range
            normalized_volume = rms / 32767.0
            
            return normalized_volume > self.config.silence_threshold
            
        except Exception as e:
            self.logger.error(f"Error processing audio chunk: {e}")
            return False
    
    def _detect_silence(self, audio_chunk: bytes) -> bool:
        """Detect silence in audio chunk."""
        return not self._process_audio_chunk(audio_chunk)
    
    def get_available_devices(self) -> List[dict]:
        """Get list of available audio input devices."""
        devices = []
        
        if not self.pyaudio:
            try:
                import pyaudio
                pa = pyaudio.PyAudio()
            except ImportError:
                self.logger.error("PyAudio not available")
                return devices
        else:
            pa = self.pyaudio
        
        try:
            device_count = pa.get_device_count()
            
            for i in range(device_count):
                device_info = pa.get_device_info_by_index(i)
                
                # Only include input devices
                if device_info.get('maxInputChannels', 0) > 0:
                    devices.append({
                        'index': i,
                        'name': device_info.get('name', f'Device {i}'),
                        'channels': device_info.get('maxInputChannels', 1),
                        'sample_rate': device_info.get('defaultSampleRate', 44100),
                        'host_api': device_info.get('hostApi', 0)
                    })
            
            # Clean up if we created a temporary PyAudio instance
            if not self.pyaudio:
                pa.terminate()
                
        except Exception as e:
            self.logger.error(f"Error enumerating audio devices: {e}")
        
        return devices
    
    def get_volume_level(self) -> float:
        """Get current volume level (0.0 to 1.0)."""
        if hasattr(self, '_last_volume'):
            return self._last_volume
        return 0.0