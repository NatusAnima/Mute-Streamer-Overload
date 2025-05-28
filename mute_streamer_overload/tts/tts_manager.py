import pyttsx3
import threading
import queue
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TTSManager:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.is_speaking = False
        self.stop_speaking = False
        self.speech_queue = queue.Queue()
        self.speech_thread: Optional[threading.Thread] = None
        self.current_wpm = 200  # Default WPM
        
        # Configure the engine
        self._configure_engine()
        
    def _configure_engine(self):
        """Configure the TTS engine with a female voice"""
        voices = self.engine.getProperty('voices')
        # Try to find a female voice
        female_voice = None
        for voice in voices:
            # Different systems might have different ways of identifying female voices
            if 'female' in voice.name.lower() or 'woman' in voice.name.lower():
                female_voice = voice
                break
        
        if female_voice:
            self.engine.setProperty('voice', female_voice.id)
        else:
            # If no female voice is found, use the first available voice
            if voices:
                self.engine.setProperty('voice', voices[0].id)
            logger.warning("No female voice found, using default voice")
        
        # Set initial rate (will be adjusted based on WPM)
        self.engine.setProperty('rate', self._wpm_to_rate(self.current_wpm))
        
    def _wpm_to_rate(self, wpm: int) -> int:
        """Convert words per minute to engine rate"""
        # The engine's rate is typically in words per minute
        # We'll use a simple conversion, but this might need tuning
        return wpm
        
    def update_wpm(self, wpm: int):
        """Update the speech rate based on WPM"""
        self.current_wpm = wpm
        self.engine.setProperty('rate', self._wpm_to_rate(wpm))
        
    def _speech_worker(self):
        """Worker thread for handling speech queue"""
        while not self.stop_speaking:
            try:
                text = self.speech_queue.get(timeout=1)
                if text is None:  # None is used as a stop signal
                    break
                    
                if not self.stop_speaking:
                    self.engine.say(text)
                    self.engine.runAndWait()
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in speech worker: {str(e)}")
                
        self.is_speaking = False
        
    def start_speaking(self):
        """Start the speech worker thread"""
        if not self.is_speaking:
            self.stop_speaking = False
            self.speech_thread = threading.Thread(target=self._speech_worker)
            self.speech_thread.daemon = True
            self.speech_thread.start()
            self.is_speaking = True
            
    def stop(self):
        """Stop the speech worker thread"""
        self.stop_speaking = True
        self.speech_queue.put(None)  # Signal the worker to stop
        if self.speech_thread and self.speech_thread.is_alive():
            self.speech_thread.join(timeout=2)
        self.is_speaking = False
        
    def speak_text(self, text: str):
        """Add text to the speech queue"""
        if self.is_speaking:
            self.speech_queue.put(text)
            
    def is_active(self) -> bool:
        """Check if TTS is currently active"""
        return self.is_speaking and not self.stop_speaking 