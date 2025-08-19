from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt

class MessageWidget(QLabel):
    def __init__(self, text, sender="user"):
        super().__init__(text)
        self.setWordWrap(True)
        self.setMaximumWidth(400)
        self.setStyleSheet(
            "background-color: #dcf8c6; padding: 8px; border-radius: 10px;"
            if sender == "user" else
            "background-color: #fff; padding: 8px; border-radius: 10px;"
        )
        self.setAlignment(Qt.AlignRight if sender == "user" else Qt.AlignLeft)
