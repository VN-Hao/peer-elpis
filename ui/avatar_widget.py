# ui/avatar_widget.py
from PyQt5.QtWidgets import QLabel, QFrame, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from voice.tts_engine import TTSEngine

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

        # Use TTS engine
        self.tts = TTSEngine(volume=volume, rate=rate)

    def speak(self, text):
        self.tts.speak(text)

    def set_volume(self, volume: float):
        self.tts.set_volume(volume)

    def set_rate(self, rate: int):
        self.tts.set_rate(rate)
