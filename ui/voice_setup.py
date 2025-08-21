import os
import sys
import time
import subprocess
import hashlib
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QProgressBar, QHBoxLayout
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal


class VoiceSetup(QWidget):
    """Pre-chat page to choose or upload peer voice and prepare an engine."""

    finished = pyqtSignal(bool)

    def __init__(self, tts_service=None, openvoice_tools_root=None):
        super().__init__()
        self.tts_service = tts_service
        self.openvoice_tools_root = openvoice_tools_root
        self.setWindowTitle('Select peer voice')
        
        # Verify OpenVoice setup first
        if not self._verify_openvoice_setup():
            return
            
        self.setup_ui()
        
    def _verify_openvoice_setup(self):
        """Verify OpenVoice installation and checkpoints."""
        openvoice_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'OpenVoice-main'))
        
        # Check required checkpoints
        required_files = {
            'Base Model': os.path.join(openvoice_root, 'checkpoints', 'base_speakers', 'EN', 'checkpoint.pth'),
            'Base Config': os.path.join(openvoice_root, 'checkpoints', 'base_speakers', 'EN', 'config.json'),
            'Converter Model': os.path.join(openvoice_root, 'checkpoints', 'converter', 'checkpoint.pth'),
            'Converter Config': os.path.join(openvoice_root, 'checkpoints', 'converter', 'config.json')
        }
        
        missing = []
        for name, path in required_files.items():
            if not os.path.exists(path):
                missing.append(f"{name} at {path}")
        
        if missing:
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel('<h2>⚠️ OpenVoice Setup Required</h2>'))
            layout.addWidget(QLabel('Missing required model files:'))
            for item in missing:
                layout.addWidget(QLabel(f'❌ {item}'))
            
            layout.addWidget(QLabel('<br><b>To complete setup:</b>'))
            layout.addWidget(QLabel('1. Download from: <a href="https://github.com/myshell-ai/OpenVoice/releases/tag/v1.0.0">OpenVoice Releases</a>'))
            layout.addWidget(QLabel('2. Get both checkpoints_1226.zip and converter.zip'))
            layout.addWidget(QLabel(f'3. Extract them to: {os.path.join(openvoice_root, "checkpoints")}'))
            
            return False
            
        return True

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        layout.addWidget(QLabel('<h2>Choose your peer\'s voice</h2>'))

        self.upload_btn = QPushButton('Upload reference audio')
        self.upload_btn.clicked.connect(self.open_file)
        layout.addWidget(self.upload_btn)

        self.engine_btn = QPushButton('Load exported engine folder')
        self.engine_btn.clicked.connect(self.open_engine_dir)
        layout.addWidget(self.engine_btn)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.status_label = QLabel('No voice selected')
        layout.addWidget(self.status_label)

        # Add save/load buttons
        save_load_layout = QHBoxLayout()
        
        self.save_btn = QPushButton('Save current engine')
        self.save_btn.clicked.connect(self.save_engine)
        self.save_btn.setEnabled(False)
        save_load_layout.addWidget(self.save_btn)
        
        self.load_saved_btn = QPushButton('Load saved engine')
        self.load_saved_btn.clicked.connect(self.load_saved_engine)
        save_load_layout.addWidget(self.load_saved_btn)
        
        layout.addLayout(save_load_layout)

        # Navigation buttons
        btn_layout = QHBoxLayout()
        self.proceed_btn = QPushButton('Proceed to chat')
        self.proceed_btn.setEnabled(False)
        self.proceed_btn.clicked.connect(lambda: self.finished.emit(True))
        btn_layout.addWidget(self.proceed_btn)
        layout.addLayout(btn_layout)

    def open_file(self):
        pth, _ = QFileDialog.getOpenFileName(self, 'Select reference audio', os.path.expanduser('~'), 'Audio Files (*.wav *.mp3)')
        if not pth:
            return
        self.status_label.setText(f'Selected: {os.path.basename(pth)}')
        # set to service so TTS engine can reference it (it will be used if OpenVoice is available)
        try:
            self.tts_service.set_voice_reference(pth)
        except Exception:
            pass

        # Start the actual export_engine.py tool in background to produce se.pth
        self.progress.setVisible(True)
        self.progress.setValue(5)
        self.proceed_btn.setEnabled(False)

        # create engine name from filename + short hash
        base = os.path.basename(pth).rsplit('.', 1)[0]
        short = hashlib.sha1(pth.encode('utf-8') + str(time.time()).encode('utf-8')).hexdigest()[:8]
        engine_name = f"{base}_{short}"

        # determine openvoice_root
        openvoice_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'OpenVoice-main'))
        
        # Create engine output directory
        engines_dir = os.path.join(openvoice_root, 'engines')
        os.makedirs(engines_dir, exist_ok=True)
        
        # Create specific engine directory
        engine_dir = os.path.join(engines_dir, engine_name)
        os.makedirs(engine_dir, exist_ok=True)

        # Use env_ov Python interpreter
        env_ov_python = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'env_ov', 'Scripts', 'python.exe'))
        if not os.path.exists(env_ov_python):
            self.status_label.setText('env_ov Python not found')
            self.progress.setVisible(False)
            return

        # Set up environment variables for the subprocess
        env = os.environ.copy()
        env['PYTHONPATH'] = os.pathsep.join([
            openvoice_root,  # Add OpenVoice-main to Python path
            os.path.join(os.path.dirname(env_ov_python), '..', 'Lib', 'site-packages'),  # Add env_ov site-packages
            env.get('PYTHONPATH', '')
        ])

        # Create and run a script that uses the OpenVoice API
        script_content = f'''
import os
import torch
from openvoice import se_extractor
from openvoice.api import BaseSpeakerTTS, ToneColorConverter

# Initialize paths
ckpt_base = os.path.join('{openvoice_root}', 'checkpoints', 'base_speakers', 'EN')
ckpt_converter = os.path.join('{openvoice_root}', 'checkpoints', 'converter')
device = "cuda:0" if torch.cuda.is_available() else "cpu"

# Initialize models
base_speaker_tts = BaseSpeakerTTS(os.path.join(ckpt_base, 'config.json'), device=device)
base_speaker_tts.load_ckpt(os.path.join(ckpt_base, 'checkpoint.pth'))

tone_color_converter = ToneColorConverter(os.path.join(ckpt_converter, 'config.json'), device=device)
tone_color_converter.load_ckpt(os.path.join(ckpt_converter, 'checkpoint.pth'))

# Create output directory path
engine_dir = os.path.join("{engines_dir}", "{engine_name}")
os.makedirs(engine_dir, exist_ok=True)

# Extract speaker embedding
target_se, audio_name = se_extractor.get_se("{pth}", tone_color_converter, target_dir=engine_dir, vad=True)

# Save model state
torch.save({{"speaker_embedding": target_se}}, os.path.join(engine_dir, "se.pth"))
'''
        script_path = os.path.join(engines_dir, f'export_{engine_name}.py')
        with open(script_path, 'w') as f:
            f.write(script_content)

        # Build command using env_ov Python
        cmd = [env_ov_python, script_path]

        # Start subprocess and log to a file in dedicated logs directory
        logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs', 'voice'))
        os.makedirs(logs_dir, exist_ok=True)
        log_path = os.path.join(logs_dir, f'export_{engine_name}.log')
        
        try:
            with open(log_path, 'wb') as logf:
                self._proc = subprocess.Popen(
                    cmd,
                    stdout=logf,
                    stderr=subprocess.STDOUT,
                    cwd=openvoice_root,
                    env=env
                )
            self._current_log_path = log_path
        except Exception as e:
            self.status_label.setText(f'Failed to start export: {e}')
            self.progress.setVisible(False)
            return

        # poll for the se.pth file
        self._engine_se_path = os.path.join(engines_dir, engine_name, 'se.pth')
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(1000)
        self._poll_timer.timeout.connect(self._poll_engine_ready)
        self._poll_timer.start()

    def open_engine_dir(self):
        pth = QFileDialog.getExistingDirectory(self, 'Select exported engine folder', os.path.expanduser('~'))
        if not pth:
            return
        self.status_label.setText(f'Engine: {os.path.basename(pth)}')
        # tell TTS service to use pre-exported engine
        try:
            self.tts_service.set_engine_dir(pth)
            self.proceed_btn.setEnabled(True)
            self.progress.setVisible(False)
        except Exception:
            self.status_label.setText('Failed to load engine')

    def save_engine(self):
        """Save the current engine to a user-selected location."""
        if not hasattr(self, '_engine_se_path') or not os.path.exists(self._engine_se_path):
            self.status_label.setText('No engine available to save')
            return
            
        save_dir = QFileDialog.getExistingDirectory(self, 'Select directory to save engine', os.path.expanduser('~'))
        if not save_dir:
            return
            
        try:
            # Create a subdirectory with voice name
            voice_name = os.path.basename(os.path.dirname(self._engine_se_path))
            save_path = os.path.join(save_dir, voice_name)
            os.makedirs(save_path, exist_ok=True)
            
            # Copy the engine files
            import shutil
            shutil.copy2(self._engine_se_path, os.path.join(save_path, 'se.pth'))
            
            self.status_label.setText(f'Engine saved to: {save_path}')
        except Exception as e:
            self.status_label.setText(f'Failed to save engine: {e}')

    def load_saved_engine(self):
        """Load a previously saved engine."""
        engine_dir = QFileDialog.getExistingDirectory(self, 'Select saved engine directory', os.path.expanduser('~'))
        if not engine_dir:
            return
            
        se_path = os.path.join(engine_dir, 'se.pth')
        if not os.path.exists(se_path):
            self.status_label.setText('Invalid engine directory (no se.pth found)')
            return
            
        try:
            self.tts_service.set_engine_dir(engine_dir)
            self._engine_se_path = se_path
            self.status_label.setText(f'Loaded engine from: {engine_dir}')
            self.proceed_btn.setEnabled(True)
            self.save_btn.setEnabled(True)
        except Exception as e:
            self.status_label.setText(f'Failed to load engine: {e}')

    def _poll_engine_ready(self):
        # update progress by checking file existence; also watch subprocess
        try:
            if os.path.isfile(self._engine_se_path):
                self._poll_timer.stop()
                self.progress.setValue(100)
                self.status_label.setText('Engine file ready')
                # inform tts service to load engine dir
                engine_dir = os.path.dirname(self._engine_se_path)
                try:
                    self.tts_service.set_engine_dir(engine_dir)
                except Exception:
                    pass
                self.proceed_btn.setEnabled(True)
                self.save_btn.setEnabled(True)  # Enable save button when engine is ready
                return

            # if process finished with non-zero exit, show log
            if hasattr(self, '_proc') and self._proc.poll() is not None:
                rc = self._proc.returncode
                if rc != 0:
                    self._poll_timer.stop()
                    # read log from dedicated logs directory with explicit binary mode first
                    try:
                        with open(self._current_log_path, 'rb') as lf:
                            raw_bytes = lf.read()
                        # Try different encodings
                        for encoding in ['utf-8', 'latin1', 'cp1252']:
                            try:
                                logtxt = raw_bytes.decode(encoding).strip()
                                break
                            except:
                                continue
                        else:
                            logtxt = raw_bytes.decode('ascii', errors='ignore').strip()
                            
                        if 'FileNotFoundError' in logtxt and 'checkpoints' in logtxt:
                            self.status_label.setText('Missing OpenVoice model files.\nPlease download checkpoints to OpenVoice-main/checkpoints/')
                        elif 'ModuleNotFoundError' in logtxt:
                            self.status_label.setText('Python module not found. Please check OpenVoice requirements.')
                        else:
                            # Show the actual error from the log if we can find it
                            error_lines = [line for line in logtxt.splitlines() if 'Error:' in line or 'Exception:' in line]
                            if error_lines:
                                self.status_label.setText(f'Export failed: {error_lines[-1]}')
                            else:
                                self.status_label.setText(f'Export failed (rc={rc}). Check log at:\n{self._current_log_path}')
                    except Exception as e:
                        self.status_label.setText(f'Export failed (rc={rc})\nError reading log: {e}')
                    self.progress.setVisible(False)
                    return

            # update progress bar
            cur = self.progress.value()
            if cur < 95:  # leave room for final steps
                self.progress.setValue(cur + 1)

        except Exception as e:
            self.status_label.setText(f'Error checking progress: {e}')
            self.progress.setVisible(False)
            self._poll_timer.stop()
