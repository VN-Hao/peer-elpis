"""Configuration handling for OpenVoice."""

import os
import json
from typing import Any, Dict, Optional

class VoiceConfig:
    """Configuration manager for voice synthesis."""
    
    @staticmethod
    def load_config(config_path: str, symbols: list) -> Dict[str, Any]:
        """Load and validate configuration from a JSON file."""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # Extract data and model configs
        data_config = config.get('data', {})
        model_config = config.get('model', {})
        
        # Use symbols from file if present; else provided symbols
        use_symbols = config.get('symbols') if 'symbols' in config else symbols

        n_fft = data_config.get('filter_length', 1024)
        spec_bins = n_fft // 2 + 1  # e.g., 513 for 1024 FFT
        n_mels = data_config.get('n_mel_channels', 80)
        cfg = {
            'n_vocab': len(use_symbols),
            # Use raw FFT bin count required by checkpoint enc_q.pre.weight
            'spec_channels': spec_bins,
            'segment_size': 32,
            'sampling_rate': data_config.get('sampling_rate', 22050),
            'filter_length': data_config.get('filter_length', 1024),
            'hop_length': data_config.get('hop_length', 256),
            'win_length': data_config.get('win_length', 1024),
            'n_mel_channels': data_config.get('n_mel_channels', 80),
            'text_cleaners': data_config.get('text_cleaners', ['cjke_cleaners2']),
            'add_blank': data_config.get('add_blank', True),
            'cleaned_text': data_config.get('cleaned_text', True),
            'inter_channels': model_config.get('inter_channels', 192),
            'hidden_channels': model_config.get('hidden_channels', 192),
            'filter_channels': model_config.get('filter_channels', 768),
            'n_heads': model_config.get('n_heads', 2),
            'n_layers': model_config.get('n_layers', 6),
            'kernel_size': model_config.get('kernel_size', 3),
            'p_dropout': model_config.get('p_dropout', 0.1),
            'resblock': model_config.get('resblock', '1'),
            'resblock_kernel_sizes': model_config.get('resblock_kernel_sizes', [3, 7, 11]),
            'resblock_dilation_sizes': model_config.get('resblock_dilation_sizes', [[1, 3, 5]]*3),
            'upsample_rates': model_config.get('upsample_rates', [8, 8, 2, 2]),
            'upsample_initial_channel': model_config.get('upsample_initial_channel', 512),
            'upsample_kernel_sizes': model_config.get('upsample_kernel_sizes', [16, 16, 4, 4]),
            'n_speakers': data_config.get('n_speakers', 1),
            'gin_channels': model_config.get('gin_channels', 256),
            'speakers': config.get('speakers', {}),
            'symbols': use_symbols
        }
        return cfg
