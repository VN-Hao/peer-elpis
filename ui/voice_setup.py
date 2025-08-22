import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QProgressBar, 
    QHBoxLayout, QCheckBox, QGroupBox, QTextEdit, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
import threading
import time


class VoiceSetup(QWidget):
    """Pre-chat page to choose or upload peer voice and prepare an engine."""

    finished = pyqtSignal(bool)

    def __init__(self, tts_service=None, openvoice_tools_root=None):
        super().__init__()
        self.tts_service = tts_service
        self.openvoice_tools_root = openvoice_tools_root
        self.setWindowTitle('Select peer voice')
        self._engine_se_path = None
        self._poll_timer = None
        self.setup_ui()

    def setup_ui(self):
        """Build the initial voice selection UI."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        # Title
        title = QLabel("<h2>Voice Setup - Enhanced Quality</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Info about improvements
        info_text = QTextEdit()
        info_text.setMaximumHeight(80)
        info_text.setReadOnly(True)
        info_text.setHtml("""
        <p><b>✨ Enhanced Voice Quality:</b> Improved tokenization, better pronunciation mapping, 
        enhanced reference embedding, and sentence-by-sentence processing for natural speech.</p>
        """)
        layout.addWidget(info_text)

        # Reference audio section
        ref_group = QGroupBox("Reference Voice")
        ref_layout = QVBoxLayout(ref_group)
        
        self.upload_btn = QPushButton('📁 Upload Reference Audio (MP3/WAV)')
        self.upload_btn.clicked.connect(self.open_file)
        ref_layout.addWidget(self.upload_btn)
        
        # Test voice button
        self.test_btn = QPushButton('🔊 Test Voice Quality')
        self.test_btn.clicked.connect(self.test_voice)
        self.test_btn.setEnabled(False)
        ref_layout.addWidget(self.test_btn)
        
        layout.addWidget(ref_group)

        # Voice quality settings
        quality_group = QGroupBox("Quality Settings")
        quality_layout = QVBoxLayout(quality_group)
        
        self.clarity_mode = QCheckBox("🎯 Clarity Mode (Enhanced audio processing)")
        self.clarity_mode.setChecked(True)
        self.clarity_mode.toggled.connect(self.update_quality_settings)
        quality_layout.addWidget(self.clarity_mode)
        
        self.prosody_mode = QCheckBox("🎵 Prosody Enhancement (Natural intonation)")
        self.prosody_mode.setChecked(True)
        self.prosody_mode.toggled.connect(self.update_quality_settings)
        quality_layout.addWidget(self.prosody_mode)
        
        layout.addWidget(quality_group)

        # Engine management section
        engine_group = QGroupBox("Engine Management (Optional)")
        engine_layout = QVBoxLayout(engine_group)
        
        self.engine_btn = QPushButton('📂 Load Exported Engine Folder')
        self.engine_btn.clicked.connect(self.open_engine_dir)
        engine_layout.addWidget(self.engine_btn)

        # Save / Load engine controls
        save_load_layout = QHBoxLayout()
        self.save_btn = QPushButton('💾 Save Current Engine')
        self.save_btn.clicked.connect(self.save_engine)
        self.save_btn.setEnabled(False)
        save_load_layout.addWidget(self.save_btn)

        self.load_saved_btn = QPushButton('📥 Load Saved Engine')
        self.load_saved_btn.clicked.connect(self.load_saved_engine)
        save_load_layout.addWidget(self.load_saved_btn)
        
        engine_layout.addLayout(save_load_layout)
        layout.addWidget(engine_group)

        # Progress bar (placeholder for future async ops)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Status label with better styling
        self.status_label = QLabel('🔍 No voice selected')
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #f9f9f9;
            }
        """)
        layout.addWidget(self.status_label)

        # Proceed button
        btn_layout = QHBoxLayout()
        self.proceed_btn = QPushButton('✨ Start Enhanced Chat')
        self.proceed_btn.setEnabled(False)
        self.proceed_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.proceed_btn.clicked.connect(lambda: self.finished.emit(True))
        btn_layout.addWidget(self.proceed_btn)
        layout.addLayout(btn_layout)

    # ---- Actions ----
    def update_quality_settings(self):
        """Update voice quality settings when checkboxes change."""
        if hasattr(self.tts_service, '_engine') and self.tts_service._engine and hasattr(self.tts_service._engine, 'openvoice'):
            openvoice = self.tts_service._engine.openvoice
            if openvoice:
                try:
                    openvoice.set_clarity_mode(self.clarity_mode.isChecked())
                    openvoice.set_prosody_heuristics(self.prosody_mode.isChecked())
                    
                    # Update status
                    clarity = "🎯 Clarity" if self.clarity_mode.isChecked() else ""
                    prosody = "🎵 Prosody" if self.prosody_mode.isChecked() else ""
                    modes = " + ".join(filter(None, [clarity, prosody]))
                    if modes:
                        self.status_label.setText(f"✅ Voice ready - Enhanced with {modes}")
                except Exception:
                    pass

    def test_voice(self):
        """Test the current voice setup with a sample phrase."""
        if not self.tts_service:
            return
            
        # Disable test button temporarily
        self.test_btn.setEnabled(False)
        self.test_btn.setText('🔊 Testing...')
        
        def test_thread():
            try:
                # Test with the phrase we optimized
                test_text = "Hello there. This is a voice quality test."
                self.tts_service.speak(test_text)
                
                # Re-enable button after a delay
                QTimer.singleShot(3000, lambda: (
                    self.test_btn.setEnabled(True),
                    self.test_btn.setText('🔊 Test Voice Quality')
                ))
            except Exception as e:
                QTimer.singleShot(100, lambda: (
                    self.test_btn.setEnabled(True),
                    self.test_btn.setText('🔊 Test Voice Quality'),
                    self.status_label.setText(f'❌ Test failed: {str(e)}')
                ))
        
        threading.Thread(target=test_thread, daemon=True).start()

    def open_file(self):
        pth, _ = QFileDialog.getOpenFileName(self, 'Select reference audio', os.path.expanduser('~'), 'Audio Files (*.wav *.mp3)')
        if not pth:
            return
        self.status_label.setText(f'Selected reference: {os.path.basename(pth)}')
        self.progress.setVisible(True)
        self.progress.setValue(5)
        if self.tts_service:
            self.tts_service.set_voice_reference(pth)
        # Launch background cloning (embedding extraction warm-up)
        threading.Thread(target=self._run_cloning, daemon=True).start()

    def _run_cloning(self):
        # Simulate staged work; actual embedding extracted on first synth call
        stages = [15, 35, 55, 75, 90, 100]
        for v in stages:
            time.sleep(0.2)
            self.progress.setValue(v)
        # Trigger a tiny warm-up synthesis (not played) to build embedding cache
        try:
            if self.tts_service and getattr(self.tts_service, 'openvoice', None):
                import tempfile, os
                tmpd = tempfile.mkdtemp(prefix='clone_warm_')
                out = os.path.join(tmpd, 'warm.wav')
                self.tts_service.openvoice.synthesize(text='testing', reference_audio=self.tts_service._ref_audio, output_path=out)
        except Exception:
            pass
        self.progress.setVisible(False)
        self.proceed_btn.setEnabled(True)
        self.status_label.setText('Reference voice ready')

    def open_engine_dir(self):
        pth = QFileDialog.getExistingDirectory(self, 'Select exported engine folder', os.path.expanduser('~'))
        if not pth:
            return
        self.status_label.setText(f'Engine: {os.path.basename(pth)}')
        try:
            if self.tts_service:
                self.tts_service.set_engine_dir(pth)
            self.proceed_btn.setEnabled(True)
            self.progress.setVisible(False)
        except Exception:
            self.status_label.setText('Failed to load engine')

    def save_engine(self):
        if not self._engine_se_path or not os.path.exists(self._engine_se_path):
            self.status_label.setText('No engine available to save')
            return
        save_dir = QFileDialog.getExistingDirectory(self, 'Select directory to save engine', os.path.expanduser('~'))
        if not save_dir:
            return
        try:
            voice_name = os.path.basename(os.path.dirname(self._engine_se_path))
            save_path = os.path.join(save_dir, voice_name)
            os.makedirs(save_path, exist_ok=True)
            import shutil
            shutil.copy2(self._engine_se_path, os.path.join(save_path, 'se.pth'))
            self.status_label.setText(f'Engine saved to: {save_path}')
        except Exception as e:
            self.status_label.setText(f'Failed to save engine: {e}')

    def load_saved_engine(self):
        engine_dir = QFileDialog.getExistingDirectory(self, 'Select saved engine directory', os.path.expanduser('~'))
        if not engine_dir:
            return
        engine_dir = os.path.abspath(engine_dir)
        se_path = os.path.join(engine_dir, 'se.pth')
        if not os.path.exists(se_path):
            self.status_label.setText('Invalid engine directory (no se.pth found)')
            return
        try:
            if self.tts_service:
                self.tts_service.set_engine_dir(engine_dir)
            self._engine_se_path = se_path
            self.status_label.setText(f'Loaded engine from: {engine_dir}')
            self.proceed_btn.setEnabled(True)
            self.save_btn.setEnabled(True)
        except Exception as e:
            self.status_label.setText(f'Failed to load engine: {e}')

    def _poll_engine_ready(self):
        self.progress.setVisible(False)
        self.status_label.setText('Ready')
