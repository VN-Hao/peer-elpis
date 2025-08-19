from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLineEdit, QPushButton, QLabel, QSlider
)
from PyQt5.QtCore import Qt
from .message_widget import MessageWidget
from .avatar_widget import AvatarWidget
from bot.llm_bot import get_bot_response

USER_NAME = "Hao"
BOT_NAME = "Elpis"

class ChatApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chatbot App")
        self.setGeometry(200, 200, 900, 500)
        self.setStyleSheet("background-color: #f0f0f0;")
        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)

        # Left side (chat)
        chat_frame = QFrame()
        chat_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #ccc;
            }
        """)
        chat_layout = QVBoxLayout(chat_frame)

        # Scrollable chat area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)
        chat_layout.addWidget(self.scroll_area)

        # Input field
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type in...")
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        chat_layout.addLayout(input_layout)

        # Right side (avatar + controls)
        right_frame = QFrame()
        right_frame.setFixedWidth(250)
        right_layout = QVBoxLayout(right_frame)

        # Avatar
        self.avatar_widget = AvatarWidget()
        right_layout.addWidget(self.avatar_widget)

        # Volume control
        volume_label = QLabel("Volume")
        volume_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(volume_label)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)  # 0% to 100%
        self.volume_slider.setValue(100)     # default full volume
        self.volume_slider.valueChanged.connect(self.change_volume)
        right_layout.addWidget(self.volume_slider)

        # Reserved space (future file management)
        reserved_label = MessageWidget("Reserved space for file management", sender="system")
        reserved_label.setFixedHeight(150)
        right_layout.addWidget(reserved_label)

        main_layout.addWidget(chat_frame, stretch=3)
        main_layout.addWidget(right_frame, stretch=1)

    def add_message(self, text, sender="user"):
        msg = MessageWidget(text, sender)
        # Wrap in horizontal layout for alignment
        h_layout = QHBoxLayout()
        if sender == "user":
            h_layout.addStretch()
            h_layout.addWidget(msg)
        else:
            h_layout.addWidget(msg)
            h_layout.addStretch()
        self.scroll_layout.addLayout(h_layout)
        # Auto-scroll
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

        # If bot, trigger avatar speaking
        if sender == "bot":
            self.avatar_widget.speak(text)

    def send_message(self):
        user_text = self.input_field.text().strip()
        if not user_text:
            return
        self.add_message(f"{USER_NAME}: {user_text}", "user")
        self.input_field.clear()

        # Bot response
        bot_reply = get_bot_response(user_text)
        self.add_message(f"{BOT_NAME}: {bot_reply}", "bot")

    def change_volume(self, value):
        """Adjust avatar TTS volume from slider"""
        volume = value / 100.0  # convert 0-100 to 0.0-1.0
        self.avatar_widget.set_volume(volume)
