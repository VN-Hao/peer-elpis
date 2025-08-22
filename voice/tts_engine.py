import os
import sys
import time
import logging
import tempfile
import winsound
import pyttsx3
import threading
import queue
import subprocess
import shutil
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class TTSEngine:
    """
    Text-to-speech engine with OpenVoice backend for high-quality voice synthesis.

    Uses the proper two-stage OpenVoice approach:
    1. Base speaker TTS generates clean audio
    2. Tone color converter applies voice cloning if reference audio is provided
    
    Falls back to pyttsx3 if OpenVoice is not available.
    """

    def __init__(self, volume=1.0, rate=150, voice=None, pitch=50):
        self.volume = volume
        self.rate = rate
        self.voice = voice
        self.pitch = pitch
        
        # Initialize OpenVoice
        self.openvoice = None
        self._ref_audio = None
        self._style = 'default'
        
        try:
            from .openvoice_tts import OpenVoiceTTS
            self.openvoice = OpenVoiceTTS()
            logger.info("[TTSEngine] OpenVoice TTS initialized successfully")
        except Exception as e:
            logger.warning(f"[TTSEngine] OpenVoice initialization failed: {e}, falling back to pyttsx3")
            self.openvoice = None
        
        # Fallback to pyttsx3 initialization
        self._initialize_pyttsx3()
        
    def _initialize_pyttsx3(self):
        """Initialize pyttsx3 as fallback TTS engine."""
        try:
            self.engine = pyttsx3.init()
            self._set_properties()
            logger.info("[TTSEngine] pyttsx3 fallback initialized")
        except Exception as e:
            logger.error(f"[TTSEngine] Failed to initialize pyttsx3: {e}")
            self.engine = None
    
    def _set_properties(self):
        """Set pyttsx3 properties."""
        if not self.engine:
            return
        self.engine.setProperty('rate', self.rate)
        self.engine.setProperty('volume', self.volume)
        if self.voice:
            voices = self.engine.getProperty('voices')
            for v in voices:
                if self.voice in v.name:
                    self.engine.setProperty('voice', v.id)
                    break

    def speak(self, text: str, callback: Optional[Callable] = None):
        """
        Speak text using the best available TTS engine.
        
        Args:
            text: Text to speak
            callback: Optional callback function to call while speaking
        """
        if not text.strip():
            return
            
        # Try OpenVoice first
        if self._is_openvoice_available():
            try:
                self._speak_openvoice(text, callback)
                return
            except Exception as e:
                logger.warning(f"[TTSEngine] OpenVoice failed: {e}, falling back to pyttsx3")
        
        # Fallback to pyttsx3
        self._speak_pyttsx3(text, callback)
    
    def _is_openvoice_available(self):
        """Check if OpenVoice is initialized and ready."""
        return self.openvoice is not None
    
    def _speak_openvoice(self, text: str, callback: Optional[Callable] = None):
        """Use OpenVoice for high-quality speech synthesis."""
        sentences = self._split_into_sentences(text)
        full_text = ""
        
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
                
            # Add sentence to accumulated text
            full_text += sentence + ". "
            
            # Update typing animation if callback provided
            if callback:
                is_complete = (i == len(sentences) - 1)
                callback(full_text.strip(), is_complete)
            
            try:
                # Synthesize audio using OpenVoice
                audio, sample_rate = self.openvoice.synthesize_audio(
                    sentence,
                    reference_audio=self._ref_audio,
                    speaker='default',
                    language='English',
                    speed=1.0
                )
                
                # Play the audio
                self._play_audio(audio, sample_rate)
                
            except Exception as e:
                logger.error(f"[TTSEngine] OpenVoice synthesis failed for '{sentence}': {e}")
                raise
    
    def _speak_pyttsx3(self, text: str, callback: Optional[Callable] = None):
        """Use pyttsx3 as fallback TTS engine."""
        if not self.engine:
            logger.error("[TTSEngine] No TTS engine available")
            return
            
        if callback:
            # Provide typing animation for fallback too
            callback(text, True)
            
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"[TTSEngine] pyttsx3 playback failed: {e}")
    
    def _play_audio(self, audio, sample_rate):
        """Play audio array using system audio."""
        import soundfile as sf
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            sf.write(tmp_file.name, audio, sample_rate)
            
            try:
                # Use Windows winsound for audio playback
                winsound.PlaySound(tmp_file.name, winsound.SND_FILENAME)
            except Exception as e:
                logger.warning(f"[TTSEngine] Audio playback failed: {e}")
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_file.name)
                except:
                    pass

    def _split_into_sentences(self, text):
        """Split text into sentences for processing."""
        import re
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences if sentences else [text]

    def set_volume(self, volume):
        """Set speech volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        if self.engine:
            self.engine.setProperty('volume', self.volume)

    def set_rate(self, rate):
        """Set speech rate (words per minute)."""
        self.rate = max(50, min(400, rate))
        if self.engine:
            self.engine.setProperty('rate', self.rate)

    def set_voice_reference(self, path: str):
        """Set a reference audio file (wav/mp3) to mimic when OpenVoice is used."""
        if path and os.path.isfile(path):
            self._ref_audio = path
        else:
            self._ref_audio = None
            
    def set_engine_dir(self, path: str):
        """Set a pre-exported engine directory that contains se.pth."""
        self._engine_dir = path if path and os.path.isdir(path) else None

    def set_style(self, style: str):
        """Set voice style for OpenVoice (e.g., 'default', 'whispering', 'sad', ...)."""
        self._style = style or 'default'
