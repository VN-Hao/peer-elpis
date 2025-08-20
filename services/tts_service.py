from PyQt5.QtCore import QObject, pyqtSignal, QThread
from voice.tts_engine import TTSEngine

class TTSSvc(QObject):
    started = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._engine = TTSEngine()

    def speak(self, text: str):
        # run in the engine's thread if it has one, otherwise call directly
        self.started.emit()
        try:
            self._engine.speak(text)
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
