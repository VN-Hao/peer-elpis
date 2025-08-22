"""
Enhanced Voice Setup UI for chat app integration.
Provides voice sample selection, processing, and engine management.
"""
import os
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QProgressBar, 
    QHBoxLayout, QCheckBox, QGroupBox, QTextEdit, QFrame, QComboBox,
    QListWidget, QListWidgetItem, QMessageBox, QSplitter, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QIcon
from services.voice_engine_service import VoiceEngineService


class EnhancedVoiceSetup(QWidget):
    """
    Enhanced voice setup interface with sample selection, processing, and engine management.
    """
    
    # Signal emitted when voice setup is complete
    voice_ready = pyqtSignal(bool)  # success
    finished = pyqtSignal(bool)     # for compatibility
    
    def __init__(self, voice_service: VoiceEngineService = None, parent=None):
        super().__init__(parent)
        
        # Initialize voice service
        self.voice_service = voice_service or VoiceEngineService()
        self._current_sample_path = None
        self._processing = False
        
        # Connect signals
        self.voice_service.processing_started.connect(self._on_processing_started)
        self.voice_service.processing_finished.connect(self._on_processing_finished)
        self.voice_service.processing_progress.connect(self._on_processing_progress)
        self.voice_service.voice_ready.connect(self._on_voice_ready)
        
        self.setWindowTitle('Voice Setup - Select Your Character Voice')
        self.setMinimumSize(900, 600)  # Increased minimum size
        self.resize(1000, 650)  # Set default size
        self.setup_ui()
        self._load_sample_voices()
        self._load_saved_engines()
    
    def setup_ui(self):
        """Build the enhanced voice selection UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        
        # Title
        title = QLabel("🎭 Character Voice Setup")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin: 10px;")
        main_layout.addWidget(title)
        
        # Create splitter for two-panel layout
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel: Voice selection
        left_panel = self._create_voice_selection_panel()
        splitter.addWidget(left_panel)
        
        # Right panel: Engine management
        right_panel = self._create_engine_management_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions (more space for left panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([600, 400])  # Set initial sizes
        
        # Progress and status section
        status_frame = QFrame()
        status_layout = QVBoxLayout(status_frame)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Select a voice sample to get started")
        self.status_label.setStyleSheet("color: #666; font-style: italic; padding: 10px; border-radius: 4px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.status_label)
        
        main_layout.addWidget(status_frame)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)  # Add spacing between buttons
        
        self.test_voice_btn = QPushButton("🔊 Test Current Voice")
        self.test_voice_btn.setMinimumHeight(40)  # Make buttons taller
        self.test_voice_btn.clicked.connect(self._test_voice)
        self.test_voice_btn.setEnabled(False)
        button_layout.addWidget(self.test_voice_btn)
        
        button_layout.addStretch()
        
        self.use_base_btn = QPushButton("✨ Use Clean Base Speaker")
        self.use_base_btn.setMinimumHeight(40)
        self.use_base_btn.clicked.connect(self._use_base_speaker)
        button_layout.addWidget(self.use_base_btn)
        
        self.continue_btn = QPushButton("➡️ Continue to Chat")
        self.continue_btn.setMinimumHeight(40)
        self.continue_btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; font-weight: bold; }")
        self.continue_btn.setShortcut("Ctrl+Return")  # Add keyboard shortcut
        self.continue_btn.setToolTip("Continue to chat (Ctrl+Enter)")
        self.continue_btn.clicked.connect(self._continue_to_chat)
        self.continue_btn.setEnabled(False)
        button_layout.addWidget(self.continue_btn)
        
        main_layout.addLayout(button_layout)
    
    def _create_voice_selection_panel(self):
        """Create the voice sample selection panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # Sample voices section
        sample_group = QGroupBox("📁 Sample Voices")
        sample_layout = QVBoxLayout(sample_group)
        
        # Predefined sample voices list
        self.sample_list = QListWidget()
        self.sample_list.setMinimumHeight(200)  # Set minimum height
        self.sample_list.itemClicked.connect(self._on_sample_selected)
        sample_layout.addWidget(self.sample_list)
        
        # Upload custom voice section  
        upload_group = QGroupBox("📤 Upload Custom Voice")
        upload_layout = QVBoxLayout(upload_group)
        
        upload_info = QLabel("Upload your own voice sample (MP3, WAV)")
        upload_info.setStyleSheet("color: #666; font-size: 12px;")
        upload_layout.addWidget(upload_info)
        
        self.upload_btn = QPushButton('📁 Browse Audio File...')
        self.upload_btn.setMinimumHeight(35)
        self.upload_btn.clicked.connect(self._browse_audio_file)
        upload_layout.addWidget(self.upload_btn)
        
        layout.addWidget(sample_group)
        layout.addWidget(upload_group)
        
        # Voice processing options
        options_group = QGroupBox("🎛️ Processing Options")
        options_layout = QVBoxLayout(options_group)
        
        self.clarity_mode = QCheckBox("🎯 High Quality Mode")
        self.clarity_mode.setChecked(True)
        self.clarity_mode.setToolTip("Use enhanced processing for clearer audio")
        options_layout.addWidget(self.clarity_mode)
        
        self.auto_save = QCheckBox("💾 Auto-save processed voice")
        self.auto_save.setChecked(True)
        self.auto_save.setToolTip("Automatically save processed voice for future use")
        options_layout.addWidget(self.auto_save)
        
        layout.addWidget(options_group)
        return panel
    
    def _create_engine_management_panel(self):
        """Create the engine management panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # Saved engines section
        saved_group = QGroupBox("💾 Saved Voice Engines")
        saved_layout = QVBoxLayout(saved_group)
        
        saved_info = QLabel("Load previously processed voices")
        saved_info.setStyleSheet("color: #666; font-size: 12px;")
        saved_layout.addWidget(saved_info)
        
        self.saved_engines_list = QListWidget()
        self.saved_engines_list.setMinimumHeight(150)  # Set minimum height
        self.saved_engines_list.itemDoubleClicked.connect(self._load_selected_engine)
        saved_layout.addWidget(self.saved_engines_list)
        
        load_btn_layout = QHBoxLayout()
        self.load_engine_btn = QPushButton("📥 Load Selected")
        self.load_engine_btn.clicked.connect(self._load_selected_engine)
        self.load_engine_btn.setEnabled(False)
        load_btn_layout.addWidget(self.load_engine_btn)
        
        self.delete_engine_btn = QPushButton("🗑️ Delete")
        self.delete_engine_btn.clicked.connect(self._delete_selected_engine)
        self.delete_engine_btn.setEnabled(False)
        load_btn_layout.addWidget(self.delete_engine_btn)
        
        saved_layout.addLayout(load_btn_layout)
        layout.addWidget(saved_group)
        
        # Current voice info
        info_group = QGroupBox("ℹ️ Current Voice Info")
        info_layout = QVBoxLayout(info_group)
        
        self.voice_info_label = QLabel("No voice selected")
        self.voice_info_label.setWordWrap(True)
        self.voice_info_label.setStyleSheet("padding: 10px; background: #f8f9fa; border-radius: 4px;")
        info_layout.addWidget(self.voice_info_label)
        
        # Save current engine
        self.save_engine_btn = QPushButton("💾 Save Current Engine")
        self.save_engine_btn.clicked.connect(self._save_current_engine)
        self.save_engine_btn.setEnabled(False)
        info_layout.addWidget(self.save_engine_btn)
        
        layout.addWidget(info_group)
        
        # Enable list selection handlers
        self.saved_engines_list.itemSelectionChanged.connect(self._on_saved_engine_selection_changed)
        
        return panel
    
    def _load_sample_voices(self):
        """Load available sample voice files."""
        self.sample_list.clear()
        
        # Get absolute path to project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Look for sample voices in assets/sample_voice/
        sample_dir = os.path.join(project_root, "assets", "sample_voice")
        if os.path.exists(sample_dir):
            for filename in os.listdir(sample_dir):
                if filename.lower().endswith(('.mp3', '.wav', '.m4a')):
                    item = QListWidgetItem(f"🎤 {os.path.splitext(filename)[0]}")
                    item.setData(Qt.UserRole, os.path.join(sample_dir, filename))
                    item.setToolTip(f"Sample voice: {filename}")
                    self.sample_list.addItem(item)
        
        # Add any sample voices from project root (absolute paths)
        for sample_path in ["reference_voice_clone.wav", "base_speaker_clean.wav"]:
            full_path = os.path.join(project_root, sample_path)
            if os.path.exists(full_path):
                name = os.path.splitext(os.path.basename(sample_path))[0].replace('_', ' ').title()
                item = QListWidgetItem(f"🔊 {name}")
                item.setData(Qt.UserRole, full_path)
                item.setToolTip(f"Generated sample: {sample_path}")
                self.sample_list.addItem(item)
        
        # If no sample voices found, add a helpful message
        if self.sample_list.count() == 0:
            placeholder_item = QListWidgetItem("📝 No sample voices found")
            placeholder_item.setFlags(placeholder_item.flags() & ~Qt.ItemIsSelectable)
            placeholder_item.setToolTip("Upload your own voice sample or use the base speaker")
            self.sample_list.addItem(placeholder_item)
    
    def _load_saved_engines(self):
        """Load list of saved voice engines."""
        self.saved_engines_list.clear()
        
        try:
            engines = self.voice_service.list_saved_engines()
            for engine_name in engines:
                item = QListWidgetItem(f"🎭 {engine_name}")
                item.setData(Qt.UserRole, engine_name)
                self.saved_engines_list.addItem(item)
        except Exception as e:
            print(f"Error loading saved engines: {e}")
    
    def _browse_audio_file(self):
        """Browse for custom audio file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Voice Sample",
            "",
            "Audio Files (*.mp3 *.wav *.m4a);;All Files (*)"
        )
        
        if file_path:
            self._process_voice_sample(file_path)
    
    def _on_sample_selected(self, item):
        """Handle sample voice selection."""
        file_path = item.data(Qt.UserRole)
        if file_path and os.path.exists(file_path):
            self._process_voice_sample(file_path)
    
    def _process_voice_sample(self, audio_path: str):
        """Process the selected voice sample."""
        if self._processing:
            return
            
        self._current_sample_path = audio_path
        voice_name = os.path.splitext(os.path.basename(audio_path))[0]
        
        # Start processing
        success = self.voice_service.select_voice_sample(audio_path, voice_name)
        if not success:
            self.status_label.setText("❌ Failed to start voice processing")
    
    @pyqtSlot()
    def _on_processing_started(self):
        """Handle processing started."""
        self._processing = True
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.upload_btn.setEnabled(False)
        self.sample_list.setEnabled(False)
        
    @pyqtSlot(bool)
    def _on_processing_finished(self, success: bool):
        """Handle processing finished."""
        self._processing = False
        self.progress_bar.setVisible(False)
        self.upload_btn.setEnabled(True)
        self.sample_list.setEnabled(True)
        
        if success:
            self.status_label.setText("✅ Voice processing complete!")
            self._update_voice_info()
            
            # Auto-save if enabled
            if self.auto_save.isChecked() and self._current_sample_path:
                voice_name = os.path.splitext(os.path.basename(self._current_sample_path))[0]
                if self.voice_service.save_current_engine(f"auto_{voice_name}"):
                    self._load_saved_engines()
        else:
            self.status_label.setText("❌ Voice processing failed")
    
    @pyqtSlot(str)
    def _on_processing_progress(self, message: str):
        """Handle processing progress updates."""
        self.status_label.setText(f"🔄 {message}")
    
    @pyqtSlot()
    def _on_voice_ready(self):
        """Handle voice ready signal."""
        self.test_voice_btn.setEnabled(True)
        self.continue_btn.setEnabled(True)
        self.save_engine_btn.setEnabled(True)
        self._update_voice_info()
        self.voice_ready.emit(True)
    
    def _update_voice_info(self):
        """Update the current voice information display."""
        info = self.voice_service.get_current_voice_info()
        if info:
            voice_name = info.get('voice_name', 'Unknown')
            engine_type = info.get('engine_type', 'Unknown')
            ref_audio = info.get('reference_audio')
            
            info_text = f"<b>Voice:</b> {voice_name}<br>"
            info_text += f"<b>Engine:</b> {engine_type}<br>"
            
            if ref_audio:
                info_text += f"<b>Reference:</b> {os.path.basename(ref_audio)}<br>"
            else:
                info_text += f"<b>Type:</b> Base Speaker (Clean)<br>"
                
            self.voice_info_label.setText(info_text)
        else:
            self.voice_info_label.setText("No voice selected")
    
    def _test_voice(self):
        """Test the current voice with a sample phrase."""
        test_text = "Hello! This is a test of the selected character voice."
        self.status_label.setText("🔊 Testing voice...")
        
        success = self.voice_service.speak_with_voice(test_text)
        if success:
            QTimer.singleShot(3000, lambda: self.status_label.setText("✅ Voice test complete"))
        else:
            self.status_label.setText("❌ Voice test failed")
    
    def _use_base_speaker(self):
        """Switch to using the clean base speaker."""
        success = self.voice_service.use_base_speaker()
        if success:
            self.status_label.setText("✅ Using clean base speaker")
            self._update_voice_info()
            self.test_voice_btn.setEnabled(True)
            self.continue_btn.setEnabled(True)
            self.save_engine_btn.setEnabled(True)
        else:
            self.status_label.setText("❌ Failed to switch to base speaker")
    
    def _save_current_engine(self):
        """Save the current voice engine."""
        from PyQt5.QtWidgets import QInputDialog
        
        engine_name, ok = QInputDialog.getText(
            self,
            "Save Voice Engine",
            "Enter a name for this voice engine:",
            text="My Voice"
        )
        
        if ok and engine_name.strip():
            success = self.voice_service.save_current_engine(engine_name.strip())
            if success:
                self.status_label.setText(f"✅ Engine saved as '{engine_name}'")
                self._load_saved_engines()
            else:
                self.status_label.setText("❌ Failed to save engine")
    
    def _on_saved_engine_selection_changed(self):
        """Handle saved engine selection change."""
        selected_items = self.saved_engines_list.selectedItems()
        has_selection = len(selected_items) > 0
        
        self.load_engine_btn.setEnabled(has_selection)
        self.delete_engine_btn.setEnabled(has_selection)
    
    def _load_selected_engine(self):
        """Load the selected saved engine."""
        selected_items = self.saved_engines_list.selectedItems()
        if not selected_items:
            return
            
        engine_name = selected_items[0].data(Qt.UserRole)
        success = self.voice_service.load_saved_engine(engine_name)
        
        if success:
            self.status_label.setText(f"✅ Loaded engine '{engine_name}'")
            self._update_voice_info()
            self.test_voice_btn.setEnabled(True)
            self.continue_btn.setEnabled(True)
            self.save_engine_btn.setEnabled(True)
        else:
            self.status_label.setText(f"❌ Failed to load engine '{engine_name}'")
    
    def _delete_selected_engine(self):
        """Delete the selected saved engine."""
        selected_items = self.saved_engines_list.selectedItems()
        if not selected_items:
            return
            
        engine_name = selected_items[0].data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Delete Engine",
            f"Are you sure you want to delete the voice engine '{engine_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Use absolute path through voice service
                engine_path = os.path.join(self.voice_service._engines_dir, f"{engine_name}.json")
                if os.path.exists(engine_path):
                    os.remove(engine_path)
                    self._load_saved_engines()
                    self.status_label.setText(f"✅ Deleted engine '{engine_name}'")
                else:
                    self.status_label.setText(f"❌ Engine file not found")
            except Exception as e:
                self.status_label.setText(f"❌ Failed to delete engine: {e}")
    
    def _continue_to_chat(self):
        """Continue to the chat interface."""
        if self.voice_service.is_voice_ready():
            self.finished.emit(True)
        else:
            self.status_label.setText("❌ Please select a voice first")


# For backward compatibility
class VoiceSetup(EnhancedVoiceSetup):
    """Backward compatible wrapper."""
    pass
