from PyQt5.QtWidgets import QLabel, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

class MessageWidget(QLabel):
    def __init__(self, text, sender="user"):
        super().__init__(text)
        self.setWordWrap(True)
        self.setMaximumWidth(400)

        # ✅ Font (programmatic control)
        font = QFont("Segoe UI", 11)
        self.setFont(font)

        # ✅ Style depends on sender
        if sender == "user":
            # light green acrylic bubble
            self.setStyleSheet(
                "background-color: rgba(220, 248, 198, 200);"   # WhatsApp green but translucent
                "border-radius: 15px;"
                "padding: 10px;"
                "border: 1px solid rgba(255, 255, 255, 0.4);"
            )
            self.setAlignment(Qt.AlignRight)
        else:
            # white/gray acrylic bubble
            self.setStyleSheet(
                "background-color: rgba(255, 255, 255, 200);"   # translucent white
                "border-radius: 15px;"
                "padding: 10px;"
                "border: 1px solid rgba(0, 0, 0, 0.1);"
            )
            self.setAlignment(Qt.AlignLeft)

        # ✅ Drop shadow for depth
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(3)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 80))  # soft shadow
        self.setGraphicsEffect(shadow)
