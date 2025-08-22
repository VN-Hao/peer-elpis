"""
OpenVoice-based TTS implementation using the proper two-stage approach.
This integrates OpenVoice directly without external dependencies.
"""

import os
import torch
import numpy as np
import logging
from typing import Optional, Tuple
import tempfile

# Import our integrated OpenVoice classes
from .openvoice.api import BaseSpeakerTTS, ToneColorConverter
from .openvoice import se_extractor

logger = logging.getLogger(__name__)


class OpenVoiceTTS:
    """Two-stage OpenVoice TTS implementation following the official approach."""
    
    def __init__(self, device: str = None):
        self.device = device or ('cuda:0' if torch.cuda.is_available() else 'cpu')
        
        # Get absolute paths to checkpoints (fixes issue when cwd changes)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.ckpt_base = os.path.join(project_root, 'checkpoints/base_speakers/EN')
        self.ckpt_converter = os.path.join(project_root, 'checkpoints/converter')
        
        # Initialize components
        self.base_speaker_tts = None
        self.tone_color_converter = None
        self.source_se = None
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize the base speaker TTS and tone color converter."""
        try:
            # Initialize base speaker TTS
            config_path = f'{self.ckpt_base}/config.json'
            checkpoint_path = f'{self.ckpt_base}/checkpoint.pth'
            
            if not os.path.exists(config_path) or not os.path.exists(checkpoint_path):
                raise FileNotFoundError(f"Base speaker files not found: {config_path}, {checkpoint_path}")
            
            self.base_speaker_tts = BaseSpeakerTTS(config_path, device=self.device)
            self.base_speaker_tts.load_ckpt(checkpoint_path)
            
            # Initialize tone color converter
            converter_config = f'{self.ckpt_converter}/config.json'
            converter_checkpoint = f'{self.ckpt_converter}/checkpoint.pth'
            
            if not os.path.exists(converter_config) or not os.path.exists(converter_checkpoint):
                raise FileNotFoundError(f"Converter files not found: {converter_config}, {converter_checkpoint}")
            
            # Disable watermark to avoid dependency on wavmark
            self.tone_color_converter = ToneColorConverter(converter_config, device=self.device, enable_watermark=False)
            self.tone_color_converter.load_ckpt(converter_checkpoint)
            
            # Load default source speaker embedding
            source_se_path = f'{self.ckpt_base}/en_default_se.pth'
            if os.path.exists(source_se_path):
                self.source_se = torch.load(source_se_path).to(self.device)
            else:
                logger.warning(f"Source speaker embedding not found: {source_se_path}")
            
            logger.info("[OpenVoiceTTS] Successfully initialized two-stage OpenVoice TTS")
            
        except Exception as e:
            logger.error(f"[OpenVoiceTTS] Failed to initialize models: {e}")
            raise
    
    def synthesize_audio(self, text: str, reference_audio: Optional[str] = None, 
                        speaker: str = 'default', language: str = 'English', 
                        speed: float = 1.0) -> Tuple[np.ndarray, int]:
        """
        Synthesize speech using the two-stage OpenVoice approach.
        
        Args:
            text: Text to synthesize
            reference_audio: Path to reference audio file for voice cloning
            speaker: Speaker style ('default', 'friendly', 'cheerful', etc.)
            language: Language ('English', 'Chinese')
            speed: Speech speed multiplier
            
        Returns:
            Tuple[np.ndarray, int]: (audio_data, sample_rate)
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Stage 1: Generate base audio with base speaker TTS
            base_audio_path = os.path.join(temp_dir, 'base_audio.wav')
            
            logger.info(f"[OpenVoiceTTS] Stage 1: Generating base audio for: '{text}'")
            self.base_speaker_tts.tts(
                text, 
                base_audio_path, 
                speaker=speaker, 
                language=language, 
                speed=speed
            )
            
            if not os.path.exists(base_audio_path):
                raise RuntimeError("Base audio generation failed")
            
            # If no reference audio, return the base audio
            if not reference_audio or not os.path.exists(reference_audio):
                logger.info("[OpenVoiceTTS] No reference audio provided, using base speaker voice")
                import soundfile as sf
                audio, sr = sf.read(base_audio_path)
                return audio, sr
            
            # Stage 2: Extract target speaker embedding and convert tone color
            logger.info(f"[OpenVoiceTTS] Stage 2: Extracting tone color from: {reference_audio}")
            
            # Use simple extraction method without VAD if whisper dependencies are not available
            try:
                target_se = self.tone_color_converter.extract_se([reference_audio])
                if target_se is None:
                    raise RuntimeError("Failed to extract speaker embedding")
            except Exception as e:
                logger.warning(f"[OpenVoiceTTS] Tone color extraction failed: {e}, using base voice")
                import soundfile as sf
                audio, sr = sf.read(base_audio_path)
                return audio, sr
            
            # Convert tone color
            output_path = os.path.join(temp_dir, 'final_output.wav')
            
            logger.info("[OpenVoiceTTS] Converting tone color...")
            self.tone_color_converter.convert(
                audio_src_path=base_audio_path,
                src_se=self.source_se,
                tgt_se=target_se,
                output_path=output_path,
                message="@peer-elpis"  # Simple watermark message
            )
            
            if not os.path.exists(output_path):
                logger.warning("[OpenVoiceTTS] Tone color conversion failed, using base audio")
                import soundfile as sf
                audio, sr = sf.read(base_audio_path)
                return audio, sr
            
            # Load final audio
            import soundfile as sf
            audio, sr = sf.read(output_path)
            
            logger.info(f"[OpenVoiceTTS] Success: Generated {len(audio)} samples at {sr} Hz")
            return audio, sr
    
    def set_speaker_style(self, style: str = 'default'):
        """
        Set the speaker style and update source embedding accordingly.
        
        Args:
            style: Speaker style ('default' or style-based like 'friendly', 'cheerful', etc.)
        """
        try:
            if style == 'default':
                source_se_path = f'{self.ckpt_base}/en_default_se.pth'
            else:
                # For style-based speakers, use the style embedding
                source_se_path = f'{self.ckpt_base}/en_style_se.pth'
            
            if os.path.exists(source_se_path):
                self.source_se = torch.load(source_se_path).to(self.device)
                logger.info(f"[OpenVoiceTTS] Updated source embedding for style: {style}")
            else:
                logger.warning(f"[OpenVoiceTTS] Source embedding not found for style: {style}")
                
        except Exception as e:
            logger.error(f"[OpenVoiceTTS] Failed to set speaker style: {e}")
