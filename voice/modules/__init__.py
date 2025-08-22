"""
OpenVoice synthesis module initialization.
"""

from .voice_synth import VoiceSynthesizer
# SynthesizerTrn now lives in internal_openvoice.models; not re-exported to avoid confusion
from .text_utils import text_to_sequence, clean_text
from .generator import Generator, ResBlock

__all__ = [
    'VoiceSynthesizer',
    'text_to_sequence',
    'clean_text',
    'Generator',
    'ResBlock',
]
