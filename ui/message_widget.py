from PyQt5.QtWidgets import QLabel, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor

class MessageWidget(QLabel):
    textUpdated = pyqtSignal(str)
    
    def __init__(self, text, sender="user"):
        super().__init__("")  # Start empty for typing animation
        self.full_text = text
        self.current_text = ""
        self.is_typing = False
        self.typing_timer = QTimer(self)  # Parent the timer to this widget
        self.typing_timer.timeout.connect(self._update_typing)
        
        # Connect our own text update signal to setText
        self.textUpdated.connect(self.setText)
        
        self.setWordWrap(True)
        self.setMaximumWidth(400)
        
        if sender != "user":
            # Start typing animation for bot messages
            self.start_typing()
        else:
            # Show user messages immediately
            self.setText(text)

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
        
    def start_typing(self):
        """Start the typing animation."""
        self.is_typing = True
        self.current_text = ""
        self.typing_timer.start(50)  # Update every 50ms
        
    def stop_typing(self):
        """Stop the typing animation and show full text."""
        self.is_typing = False
        self.typing_timer.stop()
        self.setText(self.full_text)
        
    def set_text(self, text, is_complete=False):
        """Update the text content with optional typing animation."""
        self.full_text = text
        if is_complete:
            self.stop_typing()
        else:
            self.current_text = ""
            self.start_typing()
            
    def _update_typing(self):
        """Update the typing animation."""
        if len(self.current_text) < len(self.full_text):
            # Add one character at a time
            self.current_text = self.full_text[:len(self.current_text) + 1]
            self.textUpdated.emit(self.current_text)
        else:
            self.typing_timer.stop()
            
    def safe_set_text(self, text, is_complete=False):
        """Thread-safe method to update text content."""
        self.full_text = text
        if is_complete:
            self.textUpdated.emit(text)
            self.typing_timer.stop()
        else:
            self.current_text = ""
            if not self.typing_timer.isActive():
                self.typing_timer.start(30)  # Faster typing speed (30ms)
