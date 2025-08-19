from PyQt5.QtWidgets import QLabel, QFrame, QVBoxLayout
from PyQt5.QtCore import QTimer, Qt
import pyttsx3
import threading

class AvatarWidget(QFrame):
    def __init__(self, volume=1.0, rate=150):
        super().__init__()
        self.setStyleSheet("background-color: #ddd; border-radius: 10px;")
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)

        # Avatar head
        self.avatar_label = QLabel("Avatar")
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setStyleSheet("background-color: #aaa; border-radius: 50px; font-size: 16px;")
        self.avatar_label.setFixedSize(100, 100)
        self.layout.addWidget(self.avatar_label)

        # Mouth placeholder
        self.mouth_label = QLabel("")
        self.mouth_label.setAlignment(Qt.AlignCenter)
        self.mouth_label.setStyleSheet("background-color: #f00; border-radius: 5px;")
        self.mouth_label.setFixedSize(40, 10)
        self.layout.addWidget(self.mouth_label)

        # Mouth animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_mouth)
        self.mouth_open = False

        # Default TTS settings
        self.volume = volume
        self.rate = rate

    def speak(self, text):
        # Start mouth animation
        self.timer.start(200)
        duration = max(1000, len(text) * 100)
        QTimer.singleShot(duration, self.stop_mouth_animation)

        # Use separate thread to run TTS
        threading.Thread(target=self._speak_thread, args=(text,), daemon=True).start()

    def _speak_thread(self, text):
        # Create a new engine every time
        engine = pyttsx3.init()
        engine.setProperty('volume', self.volume)
        engine.setProperty('rate', self.rate)
        engine.say(text)
        engine.runAndWait()
        engine.stop()  # ensure engine is released

    def animate_mouth(self):
        if self.mouth_open:
            self.mouth_label.setFixedHeight(10)
        else:
            self.mouth_label.setFixedHeight(20)
        self.mouth_open = not self.mouth_open

    def stop_mouth_animation(self):
        self.timer.stop()
        self.mouth_label.setFixedHeight(10)

    def set_volume(self, volume: float):
        """Adjust TTS volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(volume, 1.0))

    def set_rate(self, rate: int):
        """Adjust speech speed"""
        self.rate = rate
