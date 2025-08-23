import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLineEdit, QPushButton, QLabel, QSlider, QSizePolicy, QSplitter, QComboBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
from .message_widget import MessageWidget
from .avatar_widget import AvatarWidget
from .enhanced_voice_setup import EnhancedVoiceSetup
from .avatar_view_control import AvatarViewControl
from bot.llm_bot import get_bot_response
from controllers.avatar_controller import AvatarController
from services.voice_engine_service import VoiceEngineService
from services.llm_service import LLMSvc
from config.avatar_config import avatar_config

USER_NAME = "Hao"
BOT_NAME = "Elpis"

class ChatApp(QWidget):
    def __init__(self, avatar_controller: AvatarController = None, voice_service: VoiceEngineService = None, llm: LLMSvc = None):
        super().__init__()
        self.setWindowTitle("Peer Elpis - AI Chat with Voice")
        self.setGeometry(200, 200, 1100, 700)  # Increased window size
        self.setMinimumSize(900, 600)  # Set minimum size
        self.setStyleSheet("background-color: #f0f0f0;")

        # Enhanced voice service with save/load functionality
        self._voice_service = voice_service or VoiceEngineService()
        self._llm = llm or LLMSvc()
        self._avatar_controller = avatar_controller
        
        # Avatar configuration
        self.selected_avatar = avatar_config.get_default_avatar()
        
        # Avatar view settings
        self._avatar_view_settings = None

        self.setup_ui()

    def setup_ui(self):
        # Use a stacked approach: voice setup shown first, then avatar view control, then chat UI
        self._main_layout = QHBoxLayout(self)

        self._voice_setup = EnhancedVoiceSetup(voice_service=self._voice_service)
        self._voice_setup.finished.connect(self._on_voice_setup_finished)

        # By default show the voice setup occupying the whole window
        self._main_layout.addWidget(self._voice_setup)

    def _on_voice_setup_finished(self, ok: bool):
        """Called when VoiceSetup signals finished; show avatar view control next."""
        if not ok:
            return
        try:
            # remove the voice setup widget
            self._voice_setup.setParent(None)
        except Exception:
            pass
        # Show avatar view control next
        self._show_avatar_view_control()
    
    def _show_avatar_view_control(self):
        """Show the avatar view control interface."""
        self._avatar_view_control = AvatarViewControl(avatar_name=self.selected_avatar)
        self._avatar_view_control.view_setup_complete.connect(self._on_avatar_view_finished)
        
        # Add to main layout
        self._main_layout.addWidget(self._avatar_view_control)
    
    def _on_avatar_view_finished(self):
        """Called when avatar view control is finished; show chat UI."""
        try:
            # Store the avatar view settings from the control, always use latest
            self._avatar_view_settings = self._avatar_view_control.get_view_settings()
            print(f"🎯 Avatar view settings for chat: {self._avatar_view_settings}")  # Debug
            # Update selected avatar if changed in settings
            if self._avatar_view_settings and 'avatar_name' in self._avatar_view_settings:
                self.selected_avatar = self._avatar_view_settings['avatar_name']
                print(f"🔄 Updated selected avatar to: {self.selected_avatar}")
            # Update window title with chatbot name
            if self._avatar_view_settings and 'chatbot_name' in self._avatar_view_settings:
                chatbot_name = self._avatar_view_settings['chatbot_name']
                self.setWindowTitle(f"Peer Elpis - Chat with {chatbot_name}")
                print(f"🏷️ Updated window title with chatbot name: {chatbot_name}")
            # Remove the avatar view control widget
            self._avatar_view_control.setParent(None)
        except Exception as e:
            print(f"Error in avatar view sync: {e}")
        # Build the main chat UI
        self._build_chat_ui()

    def _build_chat_ui(self):
        main_layout = self._main_layout

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
        
        # Store reference to current bot message for typing animation
        self.current_bot_message = None

        # Input field
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type in...")
        self.input_field.returnPressed.connect(self.send_message)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        chat_layout.addLayout(input_layout)

        # Right side (avatar + controls) inside a splitter so user can drag to resize
        right_frame = QFrame()
        right_frame.setMinimumWidth(160)
        right_layout = QVBoxLayout(right_frame)
        # Remove inner margins so child widgets can span the full frame width
        right_layout.setContentsMargins(0, 0, 0, 0)
        # keep controls top-aligned and compact
        right_layout.setAlignment(Qt.AlignTop)
        right_layout.setSpacing(6)

        # Top area: avatar and volume controls centered horizontally
        top_widget = QFrame()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setAlignment(Qt.AlignHCenter)
        top_layout.setSpacing(6)

        # Avatar (keep natural size)
        # If an external AvatarController wasn't provided, create one from AvatarWidget
        if self._avatar_controller is None:
            # Get avatar name from settings (if customized) or use selected avatar
            avatar_name_to_use = self.selected_avatar
            if self._avatar_view_settings and 'avatar_name' in self._avatar_view_settings:
                avatar_name_to_use = self._avatar_view_settings['avatar_name']
                
            print(f"🎭 Creating avatar widget with: {avatar_name_to_use}")
            self.avatar_widget = AvatarWidget(avatar_name=avatar_name_to_use, view_settings=self._avatar_view_settings)
            self._avatar_controller = AvatarController(self.avatar_widget)
        else:
            # extract widget for layouting if controller wraps one
            self.avatar_widget = getattr(self._avatar_controller, 'avatar_widget', None)
            # Apply view settings if available
            if self.avatar_widget and self._avatar_view_settings:
                self.avatar_widget.update_view_settings(self._avatar_view_settings)

        if self.avatar_widget is not None:
            self.avatar_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            top_layout.addWidget(self.avatar_widget, alignment=Qt.AlignHCenter)

        # Prepare icon paths (resolve relative to repository root so cwd doesn't matter)
        icons_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'icons'))
        play_icon_path = os.path.join(icons_dir, 'play.png')
        mute_icon_path = os.path.join(icons_dir, 'mute.png')
        self.icon_play = QIcon(play_icon_path) if os.path.exists(play_icon_path) else QIcon()
        self.icon_mute = QIcon(mute_icon_path) if os.path.exists(mute_icon_path) else QIcon()

    # Windows 11 style volume control (mute button on left)
        volume_layout = QHBoxLayout()
        self.mute_button = QPushButton()
        self.mute_button.setCheckable(True)
        self.mute_button.setFixedSize(30, 30)
        # show speaker icon at start (use resolved absolute path)
        self.mute_button.setIcon(self.icon_play)
        self.mute_button.clicked.connect(self.toggle_mute)
        volume_layout.addWidget(self.mute_button)

        # Volume slider (fixed length) and centered under avatar
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(160)
        self.volume_slider.valueChanged.connect(self.change_volume)
        volume_layout.addWidget(self.volume_slider)

        top_layout.addLayout(volume_layout)
        right_layout.addWidget(top_widget)

        # Reserved space (future file management) — put below avatar and volume in the right column
        reserved_label = MessageWidget("Reserved space for file management", sender="system")
        # Allow reserved area to fill full column width and height
        reserved_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        reserved_label.setMaximumWidth(16777215)
        reserved_label.setContentsMargins(8, 8, 8, 8)
        right_layout.addWidget(reserved_label, stretch=1)

        # Put chat and right frames into a horizontal splitter so the user can drag the divider
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(chat_frame)
        splitter.addWidget(right_frame)
        # Set sensible initial sizes: chat larger than the right column
        splitter.setSizes([650, 250])
        main_layout.addWidget(splitter)

    def add_message(self, text, sender="user"):
        msg = MessageWidget(text, sender)
        h_layout = QHBoxLayout()
        if sender == "user":
            h_layout.addStretch()
            h_layout.addWidget(msg)
        else:
            h_layout.addWidget(msg)
            h_layout.addStretch()
            self.current_bot_message = msg
            
        self.scroll_layout.addLayout(h_layout)
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

        if sender == "bot":
            # Use enhanced voice service with typing animation
            try:
                self._voice_service.speak_with_voice(text, typing_callback=self._update_bot_message)
            except Exception:
                # fallback to avatar widget speak if available
                if hasattr(self, 'avatar_widget') and self.avatar_widget:
                    self.avatar_widget.speak(text)
                    
    def _update_bot_message(self, text, is_complete):
        """Callback to update the bot's message during typing/speech."""
        if self.current_bot_message:
            # Use the thread-safe method to update text
            self.current_bot_message.safe_set_text(text, is_complete)
            # Schedule scroll update on the main thread
            self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            )

    def send_message(self):
        user_text = self.input_field.text().strip()
        if not user_text:
            return
        self.add_message(user_text, "user")
        self.input_field.clear()

        # Start with empty bot message to show typing animation
        bot_reply = get_bot_response(user_text)
        self.add_message(bot_reply, "bot")

    def change_volume(self, value):
        """Adjust volume and update mute button automatically."""
        volume = value / 100.0
        # route volume change through enhanced voice service
        try:
            if hasattr(self._voice_service, 'set_volume'):
                self._voice_service.set_volume(volume)
            elif hasattr(self._voice_service, '_engine') and hasattr(self._voice_service._engine, 'set_volume'):
                self._voice_service._engine.set_volume(volume)
        except Exception:
            if hasattr(self, 'avatar_widget') and self.avatar_widget:
                self.avatar_widget.set_volume(volume)

        if value == 0:
            if not self.mute_button.isChecked():
                self.mute_button.setChecked(True)
                self.mute_button.setIcon(self.icon_mute)
        else:
            if self.mute_button.isChecked():
                self.mute_button.setChecked(False)
                self.mute_button.setIcon(self.icon_play)

    def toggle_mute(self):
        """Toggle mute/unmute when button is clicked."""
        if self.mute_button.isChecked():
            # Store last volume if > 0
            self._last_volume = self.volume_slider.value() if self.volume_slider.value() > 0 else getattr(self, "_last_volume", 100)
            self.volume_slider.setValue(0)
            self.avatar_widget.set_volume(0.0)
            self.mute_button.setIcon(self.icon_mute)
        else:
            self.volume_slider.setValue(getattr(self, "_last_volume", 100))
            self.avatar_widget.set_volume(self.volume_slider.value() / 100.0)
            self.mute_button.setIcon(self.icon_play)
