from PyQt5.QtCore import QObject, pyqtSignal, QThread
from voice.tts_engine import TTSEngine

class TTSSvc(QObject):
    started = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._engine = TTSEngine()

    def speak(self, text: str, typing_callback=None):
        """
        Speak the text with optional typing animation.
        
        Args:
            text: The text to speak
            typing_callback: Optional callback function(text: str, is_complete: bool) 
                          that will be called to update the displayed text during synthesis
        """
        self.started.emit()
        try:
            self._engine.speak(text, typing_callback)
        finally:
            self.finished.emit()

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
        try:
            self._engine.set_voice_reference(path)
        except Exception:
            pass

    def set_engine_dir(self, path: str):
        """Set pre-exported OpenVoice engine directory."""
        try:
            self._engine.set_engine_dir(path)
        except Exception:
            pass
