import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QLineEdit, QPushButton, QScrollArea, QFrame
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt

class ChatApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chatbot App")
        self.setGeometry(200, 200, 900, 500)
        self.setStyleSheet("background-color: #f0f0f0;")

        # Main horizontal layout
        main_layout = QHBoxLayout(self)

        # ---------------- Left side (Chat area) ----------------
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
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("font-size: 14px; padding: 10px;")
        chat_layout.addWidget(self.chat_area)

        # Input field
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type in...")
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)

        chat_layout.addLayout(input_layout)

        # ---------------- Right side (Avatar + Extra space) ----------------
        right_frame = QFrame()
        right_frame.setFixedWidth(250)
        right_layout = QVBoxLayout(right_frame)

        avatar_label = QLabel("Avatar")
        avatar_label.setAlignment(Qt.AlignCenter)
        avatar_label.setStyleSheet("background-color: #ddd; border-radius: 10px; font-size: 16px;")
        avatar_label.setFixedHeight(200)

        reserved_label = QLabel("Saved space to be decided later")
        reserved_label.setAlignment(Qt.AlignCenter)
        reserved_label.setStyleSheet("background-color: #ddd; border-radius: 10px; font-size: 14px;")
        reserved_label.setFixedHeight(200)

        right_layout.addWidget(avatar_label)
        right_layout.addWidget(reserved_label)

        # ---------------- Assemble ----------------
        main_layout.addWidget(chat_frame, stretch=3)
        main_layout.addWidget(right_frame, stretch=1)

    def send_message(self):
        user_text = self.input_field.text().strip()
        if user_text:
            self.chat_area.append(f"<b>You:</b> {user_text}")
            self.input_field.clear()
            # Bot reply (placeholder)
            self.chat_area.append(f"<b>Bot:</b> Hello, you said '{user_text}'!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatApp()
    window.show()
    sys.exit(app.exec_())
