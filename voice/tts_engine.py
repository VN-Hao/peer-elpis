# voice/tts_engine.py
import pyttsx3
import threading
import tempfile
import os
import time
import winsound
import logging
import subprocess

logger = logging.getLogger(__name__)

class TTSEngine:
    """
    Text-to-speech engine with an optional OpenVoice backend.

    Behavior:
    - If OpenVoice is available and properly configured in the workspace (OpenVoice-main + checkpoints),
      TTSEngine will try to synthesize using OpenVoice when a reference audio is set via
      `set_voice_reference(path)`; otherwise it falls back to pyttsx3.
    - The API is backward-compatible: call `speak(text)` to produce audio.
    """

    def __init__(self, volume=1.0, rate=150, voice=None, pitch=50, openvoice_root=None):
        self.volume = volume
        self.rate = rate
        self.voice = voice
        self.pitch = pitch

        # OpenVoice integration state
        self.openvoice_root = openvoice_root or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'OpenVoice-main'))
        self._ref_audio = None
        self._engine_dir = None
        self._style = 'default'

    def speak(self, text, typing_callback=None):
        """
        Start speaking the text with optional typing animation callback.
        
        Args:
            text: The text to speak
            typing_callback: Optional callback function(text: str, is_complete: bool) that will be called
                           to update the displayed text during synthesis
        """
        threading.Thread(
            target=self._speak_thread, 
            args=(text, typing_callback), 
            daemon=True
        ).start()

    def _speak_thread(self, text, typing_callback=None):
        # Split text into sentences for faster initial response
        sentences = self._split_into_sentences(text)
        
        # Show initial typing animation
        if typing_callback:
            typing_callback("", False)
        
        accumulated_text = ""
        for i, sentence in enumerate(sentences):
            # Update typing animation with accumulated text
            accumulated_text += sentence
            if typing_callback:
                typing_callback(accumulated_text, i == len(sentences)-1)
            
            # Synthesize and play the current sentence
            if self._is_openvoice_available() and (self._ref_audio or self._engine_dir):
                try:
                    self._speak_with_openvoice_subprocess(sentence)
                    continue
                except Exception as e:
                    logger.exception('OpenVoice synthesis (subprocess) failed, falling back to pyttsx3: %s', e)
            
            # Fallback to pyttsx3 for this sentence
            engine = pyttsx3.init()
            engine.say(sentence)
            engine.runAndWait()
            
    def _split_into_sentences(self, text):
        """Split text into sentences for incremental processing."""
        # First split on obvious sentence boundaries
        import re
        
        # Split on punctuation but keep reasonable phrases together
        parts = []
        current = []
        word_count = 0
        
        # First split on obvious boundaries
        chunks = re.split(r'([.!?]+\s+|\n+)', text)
        
        for chunk in chunks:
            if not chunk.strip():
                continue
                
            words = chunk.split()
            word_count += len(words)
            
            current.append(chunk)
            
            # Create a new part every ~8-10 words or at clear sentence boundaries
            if word_count >= 8 or chunk.rstrip()[-1] in '.!?':
                combined = ''.join(current).strip()
                if combined:
                    parts.append(combined)
                current = []
                word_count = 0
        
        # Add any remaining text
        if current:
            combined = ''.join(current).strip()
            if combined:
                parts.append(combined)
        
        return parts

        # Fallback to simple pyttsx3 synthesis
        engine = pyttsx3.init()
        engine.setProperty('volume', self.volume)
        engine.setProperty('rate', self.rate)
        if self.voice:
            try:
                engine.setProperty('voice', self.voice)
            except Exception:
                pass
        engine.say(text)
        engine.runAndWait()
        engine.stop()

    def set_volume(self, volume: float):
        self.volume = max(0.0, min(volume, 1.0))

    def set_rate(self, rate: int):
        self.rate = rate

    def set_voice_reference(self, path: str):
        """Set a reference audio file (wav/mp3) to mimic when OpenVoice is used."""
        if path and os.path.isfile(path):
            self._ref_audio = path
        else:
            self._ref_audio = None
            
    def set_engine_dir(self, path: str):
        """Set a pre-exported engine directory that contains se.pth."""
        self._engine_dir = path if path and os.path.isdir(path) else None

    def set_style(self, style: str):
        """Set voice style for OpenVoice (e.g., 'default', 'whispering', 'sad', ...)."""
        self._style = style or 'default'

    def _is_openvoice_available(self):
        """Check if OpenVoice environment and models are available."""
        # Check for env_ov Python
        env_ov_python = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'env_ov', 'Scripts', 'python.exe'))
        if not os.path.exists(env_ov_python):
            return False

        # Check for required checkpoint files
        checkpoints = [
            os.path.join(self.openvoice_root, 'checkpoints', 'base_speakers', 'EN', 'checkpoint.pth'),
            os.path.join(self.openvoice_root, 'checkpoints', 'base_speakers', 'EN', 'config.json'),
            os.path.join(self.openvoice_root, 'checkpoints', 'converter', 'checkpoint.pth'),
            os.path.join(self.openvoice_root, 'checkpoints', 'converter', 'config.json')
        ]
        return all(os.path.exists(f) for f in checkpoints)

    def _speak_with_openvoice_subprocess(self, text: str):
        """
        Run OpenVoice synthesis in a subprocess using env_ov Python.
        Uses OpenVoice-main/openvoice_engine.py with arguments:
        --text, --ref_audio, --engine_dir, --style, --output
        """
        tmp_dir = tempfile.mkdtemp(prefix='peer_elpis_ov_')
        out_path = os.path.join(tmp_dir, 'output.wav')

        # Build command
        env_ov_python = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'env_ov', 'Scripts', 'python.exe'))
        openvoice_script = os.path.join(os.path.dirname(__file__), 'openvoice_engine.py')

        # Set up environment variables for the subprocess
        env = os.environ.copy()
        env['PYTHONPATH'] = os.pathsep.join([
            self.openvoice_root,  # Add OpenVoice-main to Python path
            os.path.join(os.path.dirname(env_ov_python), '..', 'Lib', 'site-packages'),  # Add env_ov site-packages
            env.get('PYTHONPATH', '')
        ])

        cmd = [
            env_ov_python,
            openvoice_script,
            text,  # First argument is text
            out_path,  # Second argument is output path
            self._engine_dir  # Third argument is engine directory
        ]

        # Run subprocess
        try:
            # Use UTF-8 encoding explicitly for subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=60,
                env=env,
                cwd=self.openvoice_root
            )
            if result.returncode != 0:
                logger.error('OpenVoice subprocess failed: %s', result.stderr)
                raise RuntimeError('OpenVoice subprocess failed')
        except Exception as e:
            logger.exception('OpenVoice subprocess error: %s', e)
            raise

        # Wait a bit for file to be written and check if it exists
        time.sleep(0.5)
        if not os.path.exists(out_path):
            logger.error('Output file not found at: %s', out_path)
            raise RuntimeError('Output file not found')
            
        # Log file size for debugging
        file_size = os.path.getsize(out_path)
        logger.info('Generated audio file size: %d bytes', file_size)
        
        # Play resulting wav (Windows)
        try:
            # Try winsound first
            logger.info('Playing audio with winsound: %s', out_path)
            winsound.PlaySound(out_path, winsound.SND_FILENAME | winsound.SND_NODEFAULT)
        except Exception as e:
            logger.exception('winsound playback failed, trying alternative method')
            # Fallback to cmdline audio player
            try:
                subprocess.run(['powershell', '-c', f'(New-Object Media.SoundPlayer "{out_path}").PlaySync()'],
                             check=True, capture_output=True)
            except Exception as e2:
                logger.exception('Alternative playback also failed')
                raise RuntimeError(f'Audio playback failed: {e2}')
