"""
Enhanced voice engine service with save/load functionality for chat app integration.
"""
import os
import json
import pickle
import logging
import time
from typing import Optional, Dict, Any, Callable
from PyQt5.QtCore import QObject, pyqtSignal, QThread, QTimer
from voice.tts_engine import TTSEngine
from voice.openvoice_tts import OpenVoiceTTS

logger = logging.getLogger(__name__)

class VoiceEngineService(QObject):
    """
    Enhanced TTS service with voice cloning, engine saving/loading, and processing callbacks.
    """
    
    # Signals
    processing_started = pyqtSignal()
    processing_finished = pyqtSignal(bool)  # success
    processing_progress = pyqtSignal(str)   # status message
    voice_ready = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._engine = TTSEngine()
        self._current_voice_config = None
        self._is_processing = False
        
        # Use absolute path for engines directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._engines_dir = os.path.join(project_root, "saved_engines")
        
        # Ensure engines directory exists
        os.makedirs(self._engines_dir, exist_ok=True)
    
    def select_voice_sample(self, audio_path: str, voice_name: str = None) -> bool:
        """
        Select and process a voice sample for cloning.
        
        Args:
            audio_path: Path to reference audio file (mp3/wav)
            voice_name: Optional name for the voice (for saving)
            
        Returns:
            bool: True if voice selection started successfully
        """
        if self._is_processing:
            logger.warning("[VoiceEngine] Already processing, please wait")
            return False
            
        if not os.path.exists(audio_path):
            logger.error(f"[VoiceEngine] Audio file not found: {audio_path}")
            return False
        
        self._is_processing = True
        self.processing_started.emit()
        
        # Process in background thread
        self._process_voice_sample(audio_path, voice_name)
        return True
    
    def _process_voice_sample(self, audio_path: str, voice_name: str = None):
        """Process voice sample in background."""
        try:
            self.processing_progress.emit("Analyzing voice sample...")
            
            # Set the reference audio in the TTS engine
            self._engine.set_voice_reference(audio_path)
            
            # Test synthesis to ensure everything works
            self.processing_progress.emit("Testing voice synthesis...")
            test_text = "Hello, this is a voice test."
            
            if self._engine._is_openvoice_available():
                # Test with OpenVoice
                audio, sr = self._engine.openvoice.synthesize_audio(
                    test_text,
                    reference_audio=audio_path,
                    speaker='default',
                    language='English',
                    speed=1.0
                )
                self.processing_progress.emit("Voice processing complete!")
            else:
                # Fallback test
                self.processing_progress.emit("Using fallback voice engine...")
            
            # Store current configuration
            self._current_voice_config = {
                'reference_audio': audio_path,
                'voice_name': voice_name or os.path.basename(audio_path),
                'timestamp': int(time.time()),
                'engine_type': 'openvoice' if self._engine._is_openvoice_available() else 'pyttsx3'
            }
            
            self._is_processing = False
            self.processing_finished.emit(True)
            self.voice_ready.emit()
            
        except Exception as e:
            logger.error(f"[VoiceEngine] Voice processing failed: {e}")
            self._is_processing = False
            self.processing_finished.emit(False)
    
    def speak_with_voice(self, text: str, typing_callback: Optional[Callable] = None) -> bool:
        """
        Speak text using the configured voice.
        
        Args:
            text: Text to speak
            typing_callback: Optional callback for typing animation
            
        Returns:
            bool: True if speaking started successfully
        """
        if not text.strip():
            return False
            
        try:
            self._engine.speak(text, typing_callback)
            return True
        except Exception as e:
            logger.error(f"[VoiceEngine] Speech synthesis failed: {e}")
            return False
    
    def save_current_engine(self, engine_name: str) -> bool:
        """
        Save the current voice engine configuration and models.
        
        Args:
            engine_name: Name for the saved engine
            
        Returns:
            bool: True if saved successfully
        """
        if not self._current_voice_config:
            logger.error("[VoiceEngine] No voice configuration to save")
            return False
        
        try:
            engine_path = os.path.join(self._engines_dir, f"{engine_name}.json")
            
            save_data = {
                'name': engine_name,
                'config': self._current_voice_config,
                'version': '1.0',
                'saved_at': int(time.time())
            }
            
            with open(engine_path, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            logger.info(f"[VoiceEngine] Engine saved: {engine_path}")
            return True
            
        except Exception as e:
            logger.error(f"[VoiceEngine] Failed to save engine: {e}")
            return False
    
    def load_saved_engine(self, engine_name: str) -> bool:
        """
        Load a previously saved voice engine.
        
        Args:
            engine_name: Name of the engine to load
            
        Returns:
            bool: True if loaded successfully
        """
        try:
            engine_path = os.path.join(self._engines_dir, f"{engine_name}.json")
            
            if not os.path.exists(engine_path):
                logger.error(f"[VoiceEngine] Saved engine not found: {engine_path}")
                return False
            
            with open(engine_path, 'r') as f:
                save_data = json.load(f)
            
            config = save_data['config']
            reference_audio = config['reference_audio']
            
            # Check if reference audio still exists
            if not os.path.exists(reference_audio):
                logger.error(f"[VoiceEngine] Reference audio not found: {reference_audio}")
                return False
            
            # Restore the configuration
            self._engine.set_voice_reference(reference_audio)
            self._current_voice_config = config
            
            logger.info(f"[VoiceEngine] Engine loaded: {engine_name}")
            self.voice_ready.emit()
            return True
            
        except Exception as e:
            logger.error(f"[VoiceEngine] Failed to load engine: {e}")
            return False
    
    def list_saved_engines(self) -> list:
        """Get list of saved engine names."""
        try:
            engines = []
            for filename in os.listdir(self._engines_dir):
                if filename.endswith('.json'):
                    engine_name = filename[:-5]  # Remove .json
                    engines.append(engine_name)
            return engines
        except Exception as e:
            logger.error(f"[VoiceEngine] Failed to list engines: {e}")
            return []
    
    def get_current_voice_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the currently loaded voice."""
        return self._current_voice_config
    
    def is_voice_ready(self) -> bool:
        """Check if a voice is ready for synthesis."""
        return self._current_voice_config is not None
    
    def use_base_speaker(self) -> bool:
        """Switch to using the base speaker (no voice cloning)."""
        try:
            self._engine.set_voice_reference(None)
            self._current_voice_config = {
                'reference_audio': None,
                'voice_name': 'Base Speaker',
                'timestamp': int(time.time()),
                'engine_type': 'openvoice_base'
            }
            logger.info("[VoiceEngine] Switched to base speaker")
            self.voice_ready.emit()
            return True
        except Exception as e:
            logger.error(f"[VoiceEngine] Failed to switch to base speaker: {e}")
            return False

    def set_volume(self, volume: float):
        """Set voice volume (0.0 to 1.0)."""
        try:
            self._engine.set_volume(volume)
        except Exception as e:
            logger.warning(f"[VoiceEngine] Failed to set volume: {e}")
    
    def set_rate(self, rate: float):
        """Set voice rate/speed."""
        try:
            self._engine.set_rate(rate)
        except Exception as e:
            logger.warning(f"[VoiceEngine] Failed to set rate: {e}")


# For backward compatibility
class TTSSvc(VoiceEngineService):
    """Backward compatible wrapper for the enhanced voice engine service."""
    
    started = pyqtSignal()
    finished = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Map new signals to old ones for compatibility
        self.processing_started.connect(self.started.emit)
        self.processing_finished.connect(lambda success: self.finished.emit())
    
    def speak(self, text: str, typing_callback=None):
        """Legacy speak method for backward compatibility."""
        self.started.emit()
        try:
            success = self.speak_with_voice(text, typing_callback)
        finally:
            self.finished.emit()
        return success
    
    def set_volume(self, v: float):
        try:
            self._engine.set_volume(v)
        except Exception:
            pass
    
    def set_rate(self, r: float):
        try:
            self._engine.set_rate(r)
        except Exception:
            pass
    
    def set_voice_reference(self, path: str):
        """Set reference audio for voice cloning."""
        return self.select_voice_sample(path)
    
    def set_engine_dir(self, path: str):
        """Set pre-exported OpenVoice engine directory."""
        try:
            self._engine.set_engine_dir(path)
        except Exception:
            pass
