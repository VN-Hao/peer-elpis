# voice/tts_engine.py
import pyttsx3
import threading

# voice/tts_engine.py
class TTSEngine:
    def __init__(self, volume=1.0, rate=150, voice=None, pitch=50):
        self.volume = volume
        self.rate = rate
        self.voice = voice
        self.pitch = pitch

    def speak(self, text):
        threading.Thread(target=self._speak_thread, args=(text,), daemon=True).start()

    def _speak_thread(self, text):
        engine = pyttsx3.init()
        engine.setProperty('volume', self.volume)
        engine.setProperty('rate', self.rate)
        if self.voice:
            engine.setProperty('voice', self.voice)
        engine.say(text)
        engine.runAndWait()
        engine.stop()

    # <-- Add this
    def set_volume(self, volume: float):
        self.volume = max(0.0, min(volume, 1.0))

    def set_rate(self, rate: int):
        self.rate = rate
