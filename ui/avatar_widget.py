from PyQt5.QtWidgets import QLabel, QFrame, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import pyttsx3
import threading

class AvatarWidget(QFrame):
    def __init__(self, avatar_path="assets/avatar.png", volume=1.0, rate=150):
        super().__init__()
        self.setStyleSheet("background-color: #ddd; border-radius: 10px;")
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)

        # Avatar head (static image)
        self.avatar_label = QLabel()
        self.avatar_label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(avatar_path)
        self.avatar_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.layout.addWidget(self.avatar_label)

        self.volume = volume
        self.rate = rate

    def speak(self, text):
        threading.Thread(target=self._speak_thread, args=(text,), daemon=True).start()

    def _speak_thread(self, text):
        engine = pyttsx3.init()
        engine.setProperty('volume', self.volume)
        engine.setProperty('rate', self.rate)
        engine.say(text)
        engine.runAndWait()
        engine.stop()

    def set_volume(self, volume: float):
        self.volume = max(0.0, min(volume, 1.0))

    def set_rate(self, rate: int):
        self.rate = rate
