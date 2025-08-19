from PyQt5.QtWidgets import QLabel, QFrame, QVBoxLayout
from PyQt5.QtCore import Qt

class AvatarWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #ddd; border-radius: 10px;")
        self.layout = QVBoxLayout(self)
        self.avatar_label = QLabel("Avatar")
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.avatar_label)

    def speak(self, text):
        # Placeholder for speaking & lip movement
        print("Avatar speaking:", text)
        # Future: integrate TTS + lip-sync animation
