"""VoiceSynthesizer wrapper matching tts_engine expectations.

Now backed by an internal port of the full OpenVoice synthesizer (text encoder,
stochastic+deterministic duration predictors, flow prior, posterior encoder,
and generator). External third_party OpenVoice is no longer required for base
TTS synthesis once checkpoints are migrated.
"""

import os
import sys
import json
import torch
import logging
import soundfile as sf
import hashlib
import librosa
import numpy as np
import warnings
from typing import Optional, Tuple
from typing import List
from pathlib import Path

from ..internal_openvoice.models import SynthesizerTrn
from ..internal_openvoice import commons
from .text.symbols import symbols as default_symbols
from .text import text_to_sequence, cleaned_text_to_sequence
try:
    from phonemizer import phonemize as _phonemize
except ImportError:  # optional
    _phonemize = None
try:
    # g2p for English grapheme-to-phoneme (g2p-en lightweight)
    from g2p_en import G2p as _G2p
except ImportError:
    _G2p = None

logger = logging.getLogger(__name__)


class VoiceSynthesizer:
    """In-repo synthesizer using internal_openvoice implementation."""

    def __init__(self, model_path: str = None, config: dict = None, device: str = None):
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.config = config or {}
        self.model = None
        self._missing_keys = []
        self._ref_enc_untrained = False
        self._using_enhanced_pseudo = False  # Track if we're using enhanced pseudo embedding
        # Setup symbol mapping early
        if isinstance(self.config, dict):
            cfg_symbols = self.config.get('symbols') or self.config.get('symbols_list')
        else:
            cfg_symbols = None
        self.symbols = cfg_symbols if cfg_symbols else default_symbols
        self.sym2id = {s: i for i, s in enumerate(self.symbols)}
        self.blank_id = 0 if self.symbols and self.symbols[0] in {'_', ''} else None
        self._openvoice_available = self._ensure_openvoice_on_path()
        # Fallback IPA (approx) for high-frequency words; ensure symbols exist in symbols.py
        self._fallback_ipa = {
            'nice': 'naɪs',
            'meet': 'miːt',
            'you': 'juː',
            'hello': 'həloʊ',   # prefer explicit diphthong ending (approx: o + ʊ)
            'there': 'ðɛr',     # Use regular 'r' for better compatibility
            'hi': 'haɪ',
            'hey': 'heɪ'
        }
        
        # Add alternative character mappings for missing IPA symbols
        self._ipa_alternatives = {
            'r': ['r', 'ɹ', 'ɾ'],  # Try regular r first, then IPA variants
            'ɛ': ['ɛ', 'e'],        # Try IPA epsilon, then regular e
            'ð': ['ð', 'th'],       # Try eth, then 'th' digraph
            'ʊ': ['ʊ', 'u'],        # Try IPA upsilon, then regular u
            'ə': ['ə', 'a'],         # Try schwa, then regular a
            'ː': ['ː', '']           # Try long vowel marker, then skip if missing
        }
        self._load_model(model_path)
        self._g2p = None
        # Runtime tuning flags
        self.clarity_mode = True  # reduce noise & normalize output
        self.enable_prosody_heuristics = True

    def set_clarity_mode(self, enabled: bool):
        self.clarity_mode = bool(enabled)

    def set_prosody_heuristics(self, enabled: bool):
        self.enable_prosody_heuristics = bool(enabled)

    def _ensure_openvoice_on_path(self) -> bool:
        # Allow fast opt-out for debugging slow imports
        if os.environ.get('VOICESYNTH_SKIP_OPENVOICE') == '1':
            return False
        try:
            import openvoice  # noqa: F401
            return True
        except Exception:
            root = Path(__file__).resolve().parents[2]
            cand = root / 'third_party' / 'OpenVoice-main'
            if cand.exists() and str(cand) not in sys.path:
                sys.path.insert(0, str(cand))
            try:
                import openvoice  # noqa: F401
                return True
            except Exception:
                return False

    def _load_model(self, model_path: Optional[str]):
        # Build default hyper-params from config
        cfg = self.config
        try:
            # Pre-scan checkpoint (if present) to see if reference encoder weights exist
            enable_ref_enc = False
            ckpt_state = None
            if model_path and os.path.isfile(model_path):
                try:
                    raw_ckpt = torch.load(model_path, map_location='cpu')
                    ckpt_state = raw_ckpt.get('model', raw_ckpt)
                    enable_ref_enc = any(k.startswith('ref_enc.') for k in ckpt_state.keys())
                    if enable_ref_enc:
                        logger.info("[VoiceSynth] Reference encoder weights found in checkpoint")
                        self._using_enhanced_pseudo = False
                    else:
                        logger.info("[VoiceSynth] Using enhanced pseudo embedding (no trained reference encoder) - voice cloning enabled")
                        self._using_enhanced_pseudo = True
                except Exception:
                    pass
            # Override symbols if config has explicit list to match checkpoint embedding indices
            symbol_list = cfg.get('symbols') or cfg.get('symbols_list')
            effective_symbols = symbol_list if symbol_list else default_symbols
            vocab_len = cfg.get('n_vocab', len(effective_symbols))
            # Use mel channel count (training default 80) unless explicitly overridden
            spec_channels = cfg.get('spec_channels') or cfg.get('data', {}).get('n_mel_channels', 80)
            
            # Auto-detect spec_channels from checkpoint if available
            if ckpt_state and 'enc_q.pre.weight' in ckpt_state:
                ckpt_spec_channels = ckpt_state['enc_q.pre.weight'].shape[1]
                if ckpt_spec_channels != spec_channels:
                    logger.info(f"[VoiceSynth] Auto-detecting spec_channels from checkpoint: {ckpt_spec_channels} (config had {spec_channels})")
                    spec_channels = ckpt_spec_channels
            
            # Clamp to feasible range (<= n_fft//2+1) if n_fft provided
            n_fft = cfg.get('filter_length') or cfg.get('data', {}).get('filter_length', 1024)
            max_bins = n_fft // 2 + 1
            if spec_channels > max_bins:
                logger.warning(f"[VoiceSynth] spec_channels {spec_channels} > max_bins {max_bins}, using {min(513, max_bins)}")
                spec_channels = min(513, max_bins)
            n_speakers = cfg.get('n_speakers', cfg.get('data', {}).get('n_speakers', 0))
            self.model = SynthesizerTrn(
                n_vocab=vocab_len,
                spec_channels=spec_channels,
                segment_size=cfg.get('segment_size', 32),
                inter_channels=cfg.get('inter_channels', 192),
                hidden_channels=cfg.get('hidden_channels', 192),
                filter_channels=cfg.get('filter_channels', 768),
                n_heads=cfg.get('n_heads', 2),
                n_layers=cfg.get('n_layers', 6),
                kernel_size=cfg.get('kernel_size', 3),
                p_dropout=cfg.get('p_dropout', 0.1),
                resblock=cfg.get('resblock', '1'),
                resblock_kernel_sizes=cfg.get('resblock_kernel_sizes', [3,7,11]),
                resblock_dilation_sizes=cfg.get('resblock_dilation_sizes', [[1,3,5],[1,3,5],[1,3,5]]),
                upsample_rates=cfg.get('upsample_rates', [8,8,2,2]),
                upsample_initial_channel=cfg.get('upsample_initial_channel', 512),
                upsample_kernel_sizes=cfg.get('upsample_kernel_sizes', [16,16,4,4]),
                n_speakers=n_speakers,
                gin_channels=cfg.get('gin_channels', 256),
                enable_ref_enc=enable_ref_enc
            ).to(self.device)
            self.model.eval()
            # Optionally load weights if a checkpoint exists (expects key 'model')
            if ckpt_state is not None:
                try:
                    missing, unexpected = self.model.load_state_dict(ckpt_state, strict=False)
                    self._missing_keys = list(missing)
                    if missing:
                        logger.warning(f"[VoiceSynth] Missing keys ({len(missing)}): {missing[:10]}{'...' if len(missing)>10 else ''}")
                        if any(k.startswith('ref_enc.') for k in missing):
                            self._ref_enc_untrained = True
                    if unexpected:
                        logger.warning(f"[VoiceSynth] Unexpected keys ({len(unexpected)}): {unexpected[:10]}{'...' if len(unexpected)>10 else ''}")
                except Exception as e:
                    logger.warning(f"Failed to load checkpoint {model_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to build internal model: {e}")
            self.model = None

    # ---------------- Tokenization -----------------
    def _phonemize_text(self, text: str, language: str = 'en-us') -> str:
        if _phonemize is None:
            return text.lower()
        try:
            # espeak IPA output; strip stress markers not in symbols if absent
            ph = _phonemize(text, language=language, backend='espeak', strip=True, preserve_punctuation=True, with_stress=True)
            ph = ph.replace("ˈ", "\u02c8").replace("ˌ", "\u02cc")  # map primary/secondary stress
            return ph
        except Exception:
            return text.lower()

    def _g2p_phonemes(self, text: str) -> list[str]:
        """English G2P using g2p-en if installed. Returns raw ARPABET tokens (may contain stress digits)."""
        if _G2p is None:
            return []
        if self._g2p is None:
            try:
                self._g2p = _G2p()
            except Exception:
                return []
        try:
            ph = self._g2p(text)
            # Keep tokens that contain at least one uppercase letter (ARPABET) even if digits present
            cleaned = [p for p in ph if any(c.isupper() for c in p)]
            return cleaned
        except Exception:
            return []

    def _arpabet_tokens_to_ids(self, tokens: list[str]) -> Tuple[list[int], set[int]]:
        """Map ARPABET tokens to internal symbol ids via IPA approximation.

        Returns tuple (ids, stressed_indices) where stressed_indices are positions
        of primary stress vowels to boost duration for rudimentary intonation.
        """
        if not tokens:
            return [], set()
        # Mapping dicts
        vowel_map = {
            'AA': ['ɑ'], 'AE': ['æ'], 'AH': ['ʌ'],  # AH will be remapped to schwa when unstressed
            'AO': ['ɔ'], 'AW': ['a', 'ʊ'], 'AY': ['a', 'ɪ'],
            'EH': ['ɛ'], 'ER': ['ɜ'], 'EY': ['e', 'ɪ'], 'IH': ['ɪ'], 'IY': ['i'], 'OW': ['o', 'ʊ'],
            'OY': ['ɔ', 'ɪ'], 'UH': ['ʊ'], 'UW': ['u']
        }
        cons_map = {
            'TH': ['θ'], 'DH': ['ð'], 'NG': ['ŋ'], 'SH': ['ʃ'], 'ZH': ['ʒ'], 'HH': ['h'],
            'CH': ['t', 'ʃ'], 'JH': ['d', 'ʒ']
        }
        stressed = set()
        ids: list[int] = []
        pos = 0
        for tok in tokens:
            if not tok:
                continue
            # Extract stress digit if any
            stress_level = None
            if tok[-1].isdigit():
                stress_level = tok[-1]
                core = tok[:-1]
            else:
                core = tok
            core = core.upper()
            seq_syms = []
            if core in vowel_map:
                seq_syms = vowel_map[core]
                # Unstressed AH -> schwa if symbol available
                if core == 'AH' and stress_level == '0' and 'ə' in self.sym2id:
                    seq_syms = ['ə']
            elif core in cons_map:
                seq_syms = cons_map[core]
            else:
                # Fallback: decompose into letters and lowercase
                seq_syms = list(core.lower())
            mapped_any = False
            for s in seq_syms:
                if s in self.sym2id:
                    ids.append(self.sym2id[s])
                    mapped_any = True
                # silently drop symbols not in vocab
            if mapped_any and stress_level == '1':
                # Mark first symbol position of this vowel/consonant cluster for stress if primary stress
                stressed.add(pos)
            pos = len(ids)
        return ids, stressed

    def debug_tokens(self, text: str) -> list[str]:
        """Return token symbols for given text (for debugging pronunciation)."""
        seq = self._text_to_ids(text)
        toks = [self.symbols[i] if i < len(self.symbols) else '?' for i in seq]
        logger.info('[VoiceSynth][DEBUG] %s -> %s', text, ''.join(toks))
        return toks

    def _text_to_ids(self, text: str, language: str = 'en-us', force_chars: bool = False) -> list[int]:
        if not hasattr(self, '_seq_cache'):
            self._seq_cache = {}
        cache_key = (text, language, force_chars)
        if cache_key in self._seq_cache:
            return self._seq_cache[cache_key]
        seq: List[int] = []
        cleaners_cfg = self.config.get('text_cleaners') or self.config.get('data', {}).get('text_cleaners') or ['cjke_cleaners2']
        if not isinstance(cleaners_cfg, list):
            cleaners_cfg = [cleaners_cfg]
        # 1. OpenVoice pipeline
        if not force_chars and self._openvoice_available:
            try:
                mark = 'EN'
                core = text
                import re as _re
                core = _re.sub(r'([a-z])([A-Z])', r'\1 \2', core)
                if not core.startswith(f'[{mark}]'):
                    core = f'[{mark}]' + core
                if not core.endswith(f'[{mark}]'):
                    core = core + f'[{mark}]'
                # Fix import path to use third_party OpenVoice
                import sys
                import os
                openvoice_path = os.path.join(os.path.dirname(__file__), '..', '..', 'third_party', 'OpenVoice-main')
                if openvoice_path not in sys.path:
                    sys.path.insert(0, openvoice_path)
                from openvoice.text import text_to_sequence as ov_text_to_sequence
                logger.debug(f"[VoiceSynth] OpenVoice processing: '{text}' -> '{core}'")
                seq = ov_text_to_sequence(core, self.config.get('symbols', self.symbols), cleaners_cfg)
                logger.debug(f"[VoiceSynth] OpenVoice result: {len(seq)} tokens: {seq}")
            except Exception as e:
                logger.debug(f"[VoiceSynth] OpenVoice processing failed: {e}")
                seq = []
        # 2. g2p-en ARPABET
        if not seq and not force_chars:
            arpabet = self._g2p_phonemes(text)
            logger.debug(f"[VoiceSynth] G2P phonemes for '{text}': {arpabet}")
            if arpabet:
                g2p_ids, stressed = self._arpabet_tokens_to_ids(arpabet)
                seq.extend(g2p_ids)
                self._last_stress_indices = stressed
                logger.debug(f"[VoiceSynth] G2P result: {len(seq)} tokens: {seq}")
            else:
                self._last_stress_indices = set()
        # 3. mini IPA fallback
        if len(seq) < 3 and not force_chars:
            logger.debug(f"[VoiceSynth] Trying IPA fallback for '{text}' (current seq length: {len(seq)})")
            # Clean text and split into words properly
            import re
            clean_text = re.sub(r'[^\w\s]', '', text.lower())  # Remove punctuation
            words = clean_text.strip().split()
            logger.debug(f"[VoiceSynth] Split into words: {words}")
            for w in words:
                ipa_seq = self._fallback_ipa.get(w)
                if ipa_seq:
                    logger.debug(f"[VoiceSynth] Found IPA for '{w}': '{ipa_seq}'")
                    for ch in ipa_seq:
                        token_id = None
                        # Try the character directly first
                        if ch in self.sym2id:
                            token_id = self.sym2id[ch]
                            seq.append(token_id)
                            logger.debug(f"[VoiceSynth]   '{ch}' -> token {token_id}")
                        else:
                            # Try alternatives if available
                            alternatives = self._ipa_alternatives.get(ch, [ch])
                            found_alternative = False
                            for alt in alternatives:
                                if alt in self.sym2id:
                                    token_id = self.sym2id[alt]
                                    seq.append(token_id)
                                    logger.debug(f"[VoiceSynth]   '{ch}' -> '{alt}' -> token {token_id}")
                                    found_alternative = True
                                    break
                            if not found_alternative:
                                logger.warning(f"[VoiceSynth]   IPA symbol '{ch}' and alternatives {alternatives} not found in symbol set")
                                # As last resort, try character fallback for just this symbol
                                if ch.lower() in self.sym2id:
                                    token_id = self.sym2id[ch.lower()]
                                    seq.append(token_id)
                                    logger.debug(f"[VoiceSynth]   '{ch}' -> lowercase '{ch.lower()}' -> token {token_id}")
                    # Add space between words (if space symbol exists)
                    if ' ' in self.sym2id and w != words[-1]:  # Don't add space after last word
                        seq.append(self.sym2id[' '])
                        logger.debug(f"[VoiceSynth]   Added space -> token {self.sym2id[' ']}")
                else:
                    logger.debug(f"[VoiceSynth] No IPA found for '{w}', trying character fallback for this word")
                    # Character fallback for this specific word
                    for ch in w:
                        if ch in self.sym2id:
                            token_id = self.sym2id[ch]
                            seq.append(token_id)
                            logger.debug(f"[VoiceSynth]   '{ch}' -> token {token_id}")
                    # Add space between words
                    if ' ' in self.sym2id and w != words[-1]:
                        seq.append(self.sym2id[' '])
            logger.debug(f"[VoiceSynth] IPA fallback result: {len(seq)} tokens: {seq}")
        # 4. character fallback
        if len(seq) < 3:
            logger.debug(f"[VoiceSynth] Using character fallback for '{text}' (seq length: {len(seq)})")
            for ch in text.lower():
                if ch in self.sym2id:
                    seq.append(self.sym2id[ch])
        add_blank = self.config.get('data', {}).get('add_blank') or self.config.get('add_blank')
        # Force blanks if explicitly requested via config override (improves alignment robustness)
        force_add_blank = self.config.get('force_add_blank', False)
        # Be more conservative with blank insertion - only add if we have a reasonable number of tokens
        # and it's not a very short sequence (which might be character fallback)
        if (add_blank or force_add_blank) and self.blank_id is not None and seq and len(seq) > 3:
            seq = commons.intersperse(seq, self.blank_id)
        elif len(seq) <= 3:
            # For very short sequences, avoid blanks as they may interfere with character-level processing
            logger.debug("[VoiceSynth] Skipping blank insertion for short sequence: %s", seq)
        self._seq_cache[cache_key] = seq
        return seq

    def _extract_reference_embedding_improved(self, reference_audio: str):
        """Extract reference embedding using OpenVoice-style spectrogram processing."""
        if not reference_audio or not os.path.exists(reference_audio):
            return None
            
        if not hasattr(self, '_ref_cache'):
            self._ref_cache = {}
        if reference_audio in self._ref_cache:
            return self._ref_cache[reference_audio]
            
        try:
            import librosa
            
            # Load audio using the same parameters as OpenVoice
            sampling_rate = self.config.get('sampling_rate', 22050)
            audio_ref, sr = librosa.load(reference_audio, sr=sampling_rate)
            
            # Convert to tensor
            y = torch.FloatTensor(audio_ref).to(self.device)
            y = y.unsqueeze(0)
            
            # Get STFT parameters from config or use OpenVoice defaults
            filter_length = self.config.get('filter_length', 1024)
            hop_length = self.config.get('hop_length', 256) 
            win_length = self.config.get('win_length', 1024)
            
            # Create spectrogram using OpenVoice-style processing
            spec = self._spectrogram_torch(y, filter_length, sampling_rate, hop_length, win_length, center=False)
            
            # Extract reference embedding using model's ref_enc
            with torch.no_grad():
                if hasattr(self.model, 'ref_enc') and self.model.ref_enc is not None:
                    # Note: removed .unsqueeze(-1) as Conv1d expects 3D tensors
                    g_latent = self.model.ref_enc(spec.transpose(1, 2))
                    self._ref_cache[reference_audio] = g_latent
                    logger.info("[VoiceSynth] Using trained reference encoder for voice cloning")
                    return g_latent
                else:
                    # No trained reference encoder - use enhanced pseudo embedding
                    logger.info("[VoiceSynth] No trained reference encoder, using enhanced pseudo embedding")
                    return self._create_enhanced_pseudo_embedding(audio_ref, sampling_rate)
                    
        except Exception as e:
            logger.warning(f"[VoiceSynth] Improved reference embedding extraction failed: {e}, falling back to basic method")
            return self._extract_reference_embedding(reference_audio)
    
    def _spectrogram_torch(self, y, n_fft, sampling_rate, hop_size, win_size, center=False):
        """OpenVoice-style spectrogram computation."""
        if torch.min(y) < -1.1:
            logger.debug("Audio min value is %f", torch.min(y))
        if torch.max(y) > 1.1:
            logger.debug("Audio max value is %f", torch.max(y))

        # Create hann window
        dtype_device = str(y.dtype) + "_" + str(y.device)
        wnsize_dtype_device = str(win_size) + "_" + dtype_device
        if not hasattr(self, '_hann_windows'):
            self._hann_windows = {}
        if wnsize_dtype_device not in self._hann_windows:
            self._hann_windows[wnsize_dtype_device] = torch.hann_window(win_size).to(
                dtype=y.dtype, device=y.device
            )

        # Padding
        y = torch.nn.functional.pad(
            y.unsqueeze(1),
            (int((n_fft - hop_size) / 2), int((n_fft - hop_size) / 2)),
            mode="reflect",
        )
        y = y.squeeze(1)

        # STFT with proper complex tensor handling for newer PyTorch versions
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            spec = torch.stft(
                y,
                n_fft,
                hop_length=hop_size,
                win_length=win_size,
                window=self._hann_windows[wnsize_dtype_device],
                center=center,
                pad_mode="reflect",
                normalized=False,
                onesided=True,
                return_complex=True,  # Use new PyTorch API
            )

        # Convert complex to magnitude
        spec = torch.abs(spec)
        return spec
    
    def _create_enhanced_pseudo_embedding(self, audio_ref, sampling_rate):
        """Create an enhanced pseudo embedding when no trained reference encoder is available."""
        try:
            # More sophisticated analysis of the reference audio
            import librosa
            
            # Extract multiple acoustic features
            features = []
            
            # 1. Spectral centroid (brightness)
            spectral_centroid = librosa.feature.spectral_centroid(y=audio_ref, sr=sampling_rate)[0]
            features.extend([
                float(np.mean(spectral_centroid)),
                float(np.std(spectral_centroid)),
                float(np.percentile(spectral_centroid, 25)),
                float(np.percentile(spectral_centroid, 75))
            ])
            
            # 2. Zero crossing rate (texture)
            zcr = librosa.feature.zero_crossing_rate(audio_ref)[0]
            features.extend([
                float(np.mean(zcr)),
                float(np.std(zcr))
            ])
            
            # 3. Spectral rolloff (timbre)
            rolloff = librosa.feature.spectral_rolloff(y=audio_ref, sr=sampling_rate)[0]
            features.extend([
                float(np.mean(rolloff)),
                float(np.std(rolloff))
            ])
            
            # 4. MFCCs (voice characteristics)
            mfccs = librosa.feature.mfcc(y=audio_ref, sr=sampling_rate, n_mfcc=12)
            for i in range(min(8, mfccs.shape[0])):  # Use first 8 MFCCs
                features.extend([
                    float(np.mean(mfccs[i])),
                    float(np.std(mfccs[i]))
                ])
            
            # 5. Fundamental frequency (pitch characteristics)  
            try:
                f0, voiced_flag, voiced_probs = librosa.pyin(audio_ref, 
                                                           fmin=librosa.note_to_hz('C2'), 
                                                           fmax=librosa.note_to_hz('C7'))
                f0_clean = f0[voiced_flag]
                if len(f0_clean) > 0:
                    features.extend([
                        float(np.mean(f0_clean)),
                        float(np.std(f0_clean)),
                        float(np.median(f0_clean))
                    ])
                else:
                    features.extend([0.0, 0.0, 0.0])
            except:
                features.extend([0.0, 0.0, 0.0])
            
            # Convert to tensor
            gin_channels = getattr(self.model, 'gin_channels', 256)
            features_tensor = torch.tensor(features, dtype=torch.float32, device=self.device)
            
            # Project to gin_channels dimensions
            if len(features) != gin_channels:
                if len(features) < gin_channels:
                    # Pad with zeros
                    padding = torch.zeros(gin_channels - len(features), device=self.device)
                    features_tensor = torch.cat([features_tensor, padding])
                else:
                    # Truncate
                    features_tensor = features_tensor[:gin_channels]
            
            # Shape should match reference encoder output: (batch_size, gin_channels, 1)
            g_latent = features_tensor.unsqueeze(0).unsqueeze(-1)  # (1, gin_channels, 1)
            
            # Normalize to reasonable range similar to original method
            g_latent = torch.nn.functional.layer_norm(g_latent, g_latent.shape[1:-1])
            g_latent = torch.tanh(g_latent * 0.5)  # Gentle scaling
            
            logger.debug(f"[VoiceSynth] Enhanced pseudo embedding shape: {g_latent.shape}")
            return g_latent
            
        except Exception as e:
            logger.warning(f"[VoiceSynth] Enhanced pseudo embedding failed: {e}")
            # Fallback to basic method
            return self._extract_reference_embedding(reference_audio)
    
    def _create_default_pseudo_embedding(self) -> torch.Tensor:
        """Create a default pseudo embedding when no reference audio is available."""
        try:
            gin_channels = getattr(self.model, 'gin_channels', 256)
            
            # Create a simple but reasonable pseudo embedding
            # Shape must be (batch_size, gin_channels, sequence_length) for Conv1d
            g_latent = torch.randn(1, gin_channels, 1, device=self.device) * 0.1
            
            # Add some structure to make it more voice-like
            # Simulate spectral envelope characteristics
            for i in range(0, gin_channels, 8):
                # Add some formant-like peaks
                g_latent[0, i:i+2, 0] += 0.3
                if i + 4 < gin_channels:
                    g_latent[0, i+4:i+6, 0] += 0.2
            
            # Normalize to reasonable range
            g_latent = g_latent / (torch.norm(g_latent, dim=1, keepdim=True) + 1e-6)  # L2 normalize
            g_latent = torch.tanh(g_latent * 0.5)
            
            logger.debug(f"[VoiceSynth] Default pseudo embedding shape: {g_latent.shape}")
            return g_latent
            
        except Exception as e:
            logger.warning(f"[VoiceSynth] Default pseudo embedding failed: {e}")
            # Ultimate fallback - simple zeros with correct shape (batch_size, gin_channels, 1)
            gin_channels = getattr(self.model, 'gin_channels', 256)
            return torch.zeros(1, gin_channels, 1, device=self.device)

    def _extract_reference_embedding(self, reference_audio: str) -> Optional[torch.Tensor]:
        """Extract a reference embedding using the internal reference encoder.

        This is a lightweight approximation: load audio -> mel spectrogram (librosa)
        -> convert to torch tensor shaped (B=1, T, spec_channels) expected by ReferenceEncoder.
        """
        if not reference_audio or not os.path.isfile(reference_audio):
            return None
        try:
            if not hasattr(self, '_ref_cache'):
                self._ref_cache = {}
            if reference_audio in self._ref_cache:
                return self._ref_cache[reference_audio]
            wav, sr = librosa.load(reference_audio, sr=self.config.get('sampling_rate', 22050))
            # Compute mel spectrogram matching expected spec_channels if possible
            n_fft = 1024
            hop = 256
            n_mels = self.config.get('data', {}).get('n_mel_channels', 80)
            if n_mels > n_fft//2 + 1:
                n_mels = 80
            mel = librosa.feature.melspectrogram(y=wav, sr=sr, n_fft=n_fft, hop_length=hop, n_mels=n_mels)
            mel = librosa.power_to_db(mel, ref=np.max)
            mel_t = torch.from_numpy(mel.T).float().unsqueeze(0).to(self.device)  # (1, T, spec_channels)
            # Path 1: true reference encoder exists & trained
            if hasattr(self.model, 'ref_enc') and not self._ref_enc_untrained:
                with torch.no_grad():
                    g_latent = self.model.ref_enc(mel_t)
                self._ref_cache[reference_audio] = g_latent
                return g_latent  # (1, gin_channels)
            # If reference encoder missing/untrained and we have speaker embeddings, skip pseudo embedding to avoid degrading clarity
            if (not hasattr(self.model, 'ref_enc') or self._ref_enc_untrained) and hasattr(self.model, 'emb_g'):
                return None
            # Path 2: pseudo embedding (deterministic) when ref_enc unavailable and no speaker embeddings (n_speakers==0)
            gin = self.config.get('gin_channels', 256)
            # Aggregate simple statistics (mean & std per mel bin)
            mean = mel_t.mean(dim=1)  # (1, spec)
            std = mel_t.std(dim=1).clamp_min(1e-5)
            stats_list = [mean, std]
            # Pitch (F0) statistics via librosa.pyin (robust for monophonic speech)
            try:
                f0, _, _ = librosa.pyin(wav, fmin=50, fmax=600, sr=sr, frame_length=n_fft, hop_length=hop)
                if f0 is not None:
                    f0_valid = f0[~np.isnan(f0)]
                    if len(f0_valid) > 5:
                        f0_t = torch.tensor([
                            float(np.mean(f0_valid)),
                            float(np.std(f0_valid) + 1e-5),
                            float(np.median(f0_valid)),
                            float(np.percentile(f0_valid, 25)),
                            float(np.percentile(f0_valid, 75)),
                            float(len(f0_valid) / (len(f0) + 1e-5))  # voiced ratio
                        ], device=self.device).unsqueeze(0)  # (1,6)
                        # Normalize log-space for stability
                        f0_t[:, :5] = torch.log(f0_t[:, :5].clamp_min(1e-3))
                        stats_list.append(f0_t)
            except Exception:
                pass
            # Energy (RMS) summary (log space) as additional style cues
            try:
                rms = librosa.feature.rms(y=wav, frame_length=n_fft, hop_length=hop)[0]
                if rms.size > 5:
                    rms_valid = rms[rms > 1e-5]
                    if rms_valid.size > 5:
                        rms_t = torch.tensor([
                            float(np.log(np.mean(rms_valid))),
                            float(np.log(np.std(rms_valid) + 1e-6)),
                            float(np.log(np.median(rms_valid))),
                        ], device=self.device).unsqueeze(0)
                        stats_list.append(rms_t)
            except Exception:
                pass
            stats = torch.cat(stats_list, dim=1)
            in_dim = stats.shape[1]
            # Lazy initialize projection matrix with deterministic seed from file hash
            if not hasattr(self, '_pseudo_proj') or self._pseudo_proj is None or self._pseudo_proj.shape != (gin, in_dim):
                h = int(hashlib.md5(reference_audio.encode('utf-8')).hexdigest(), 16) % (2**31 - 1)
                g = torch.Generator(device=self.device)
                g.manual_seed(h)
                self._pseudo_proj = torch.randn(gin, in_dim, generator=g, device=self.device) * (1.0 / in_dim**0.5)
            g_latent = torch.matmul(self._pseudo_proj, stats.transpose(0,1)).transpose(0,1)  # (1, gin)
            g_latent = torch.nn.functional.layer_norm(g_latent, g_latent.shape[-1:])
            self._ref_cache[reference_audio] = g_latent
            return g_latent
        except Exception as e:
            logger.warning(f"[VoiceSynth] Reference embedding extraction failed: {e}")
            return None

    def synthesize_audio(self, text: str, reference_audio: Optional[str] = None,
                        style: str = 'default', language: str = 'en', length_scale: float = 1.05,
                        noise_scale: float = 0.667, noise_scale_w: float = 0.9) -> Tuple[np.ndarray, int]:
        """Synthesize speech and return audio data directly.
        
        Returns:
            Tuple[np.ndarray, int]: (audio_data, sample_rate)
        """
        if not self.model:
            raise RuntimeError('Model not initialized')

        # Split text into sentences for better prosody - based on OpenVoice approach
        import re
        # More careful sentence splitting to avoid breaking short phrases
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # If no splitting occurred or text is short, treat as single sentence
        if not sentences or len(sentences) == 1 and len(text.strip()) < 100:
            sentences = [text.strip()]  # fallback to original text
            
        logger.info(f'[VoiceSynth] Processing {len(sentences)} sentence(s): {sentences}')
        
        # Get reference embedding once for all sentences - try improved method first
        g_latent = None
        use_reference_embedding = False
        if reference_audio:
            g_latent = self._extract_reference_embedding_improved(reference_audio)
            if g_latent is None:
                logger.debug("[VoiceSynth] Falling back to basic reference embedding")
                g_latent = self._extract_reference_embedding(reference_audio)
            if g_latent is not None:
                use_reference_embedding = True
        
        # Don't use pseudo embeddings for converter models - they may not support it
        if g_latent is None:
            logger.debug("[VoiceSynth] No reference audio - using base model without reference embedding")
            use_reference_embedding = False
        
        audio_segments = []
        sampling_rate = self.config.get('sampling_rate', 22050)
        
        for i, sentence in enumerate(sentences):
            # 1. Text -> ids
            seq = self._text_to_ids(sentence, language=language, force_chars=False)
            logger.info(f'[VoiceSynth] Sentence {i+1}: "{sentence}" -> {len(seq)} tokens: {seq[:20]}{"..." if len(seq) > 20 else ""}')
            if seq and self.enable_prosody_heuristics:
                vowel_chars = set('aeiou')
                decoded = ''.join([self.symbols[j] if j < len(self.symbols) else '' for j in seq])
                vowels = sum(1 for c in decoded if c in vowel_chars)
                ratio = vowels / max(1, len(decoded))
                sentence_length_scale = length_scale
                if ratio < 0.25:
                    sentence_length_scale *= 1.06
                elif ratio > 0.5:
                    sentence_length_scale *= 0.97
                if len(seq) < 12:
                    sentence_length_scale *= 1.04
            else:
                sentence_length_scale = length_scale

            # 2. Synthesize audio for this sentence
            audio_segment = self._synthesize_sequence(
                seq, 
                g_latent if use_reference_embedding else None, 
                noise_scale=noise_scale, 
                noise_scale_w=noise_scale_w,
                length_scale=sentence_length_scale
            )
            
            if audio_segment is not None:
                audio_segments.append(audio_segment)
                
                # Add pause between sentences (50ms)
                if i < len(sentences) - 1:
                    pause_samples = int(0.05 * sampling_rate)  # 50ms pause
                    silence = np.zeros(pause_samples, dtype=np.float32)
                    audio_segments.append(silence)

        if not audio_segments:
            raise RuntimeError("Failed to synthesize any audio")
        
        # Concatenate all audio segments
        final_audio = np.concatenate(audio_segments)
        return final_audio, sampling_rate

    def _synthesize_sequence(self, seq: List[int], g_latent, noise_scale: float = 0.667, 
                           noise_scale_w: float = 0.9, length_scale: float = 1.0) -> Optional[np.ndarray]:
        """Core synthesis method for a single token sequence.
        
        Args:
            seq: List of token IDs
            g_latent: Reference embedding tensor or None
            noise_scale: Noise scale for synthesis
            noise_scale_w: Noise scale W for synthesis
            length_scale: Length scale for synthesis
            
        Returns:
            Audio array or None if failed
        """
        if not seq:
            return None
            
        # Filter invalid tokens
        vocab_size = int(self.model.enc_p.emb.num_embeddings)
        before = len(seq)
        seq = [j for j in seq if 0 <= j < vocab_size]
        if len(seq) != before:
            logger.debug('[VoiceSynth] Filtered %d invalid token ids', before - len(seq))
        if not seq:
            return None

        x = torch.LongTensor(seq).unsqueeze(0).to(self.device)
        x_lengths = torch.LongTensor([x.shape[-1]]).to(self.device)
        
        # Speaker conditioning - use default speaker 0
        sid = torch.LongTensor([0]).to(self.device)

        # Synthesis with improved parameters
        with torch.no_grad():
            # Duration bias for better prosody
            duration_bias = None
            if self.enable_prosody_heuristics:
                try:
                    puncts = {',', '.', '!', '?'}
                    toks = [self.symbols[j] if j < len(self.symbols) else '' for j in seq]
                    bias = torch.zeros(1, 1, len(seq), device=self.device)
                    for idx, tk in enumerate(toks):
                        if tk in puncts and idx > 0:
                            bias[0, 0, idx-1] += 0.20  # pause emphasis
                        elif tk in 'aeiou':
                            base = 0.08  # vowel elongation
                            if idx+1 < len(toks) and toks[idx+1] in puncts:
                                base += 0.06
                            bias[0, 0, idx] += base
                        # Encourage completion by extending tokens toward the end
                        if idx >= len(toks) * 0.6:  # Last 40% of tokens
                            bias[0, 0, idx] += 0.05
                    duration_bias = bias
                except Exception:
                    pass
                    
            # Use OpenVoice-style parameters
            if self.clarity_mode:
                infer_kwargs = dict(sid=sid, length_scale=length_scale, 
                                  noise_scale=0.55, noise_scale_w=0.5, sdp_ratio=0.25)
            else:
                infer_kwargs = dict(sid=sid, length_scale=length_scale * 1.05, 
                                  noise_scale=noise_scale, noise_scale_w=noise_scale_w, sdp_ratio=0.2)
            if duration_bias is not None:
                infer_kwargs['duration_bias'] = duration_bias
            if g_latent is not None:
                infer_kwargs['g_latent'] = g_latent
                
            y_hat, attn, y_mask, meta = self.model.infer(x, x_lengths, **infer_kwargs)
            
            # Optional duration smoothing
            try:
                dur = attn.squeeze(1).sum(2).squeeze(0).cpu().numpy()
                if dur.size > 3:
                    median_dur = np.median(dur)
                    if median_dur < 1.0 and length_scale < 1.5:
                        new_scale = length_scale * 1.15
                        logger.debug(f"[VoiceSynth] Adjusting length_scale to {new_scale}")
                        infer_kwargs['length_scale'] = new_scale
                        y_hat, _, _, _ = self.model.infer(x, x_lengths, **infer_kwargs)
            except Exception as e:
                logger.debug(f"[VoiceSynth] Duration smoothing failed: {e}")
                
            audio_segment = y_hat[0, 0].data.cpu().numpy()
            
        # Post-processing
        if self.clarity_mode and audio_segment.size > 0:
            audio_segment = audio_segment - audio_segment.mean()
            peak = np.max(np.abs(audio_segment)) + 1e-9
            if peak > 0:
                audio_segment = 0.89 * audio_segment / peak
            rms = np.sqrt(np.mean(audio_segment**2) + 1e-9)
            target_rms = 0.08
            if rms < target_rms * 0.9:
                audio_segment *= (target_rms / max(rms, 1e-6))
            preemph = 0.97
            audio_segment = np.append(audio_segment[0], audio_segment[1:] - preemph * audio_segment[:-1])
            
        return audio_segment

    def synthesize(self, text: str, reference_audio: Optional[str] = None, output_path: Optional[str] = None,
                   style: str = 'default', language: str = 'en', length_scale: float = 1.05) -> bool:
        """Synthesize speech to output_path with improved sentence-by-sentence processing.

        Returns True on success, False otherwise (and logs error).
        """
        if not self.model:
            logger.error('Model not initialized')
            return False
        if not output_path:
            raise ValueError('output_path required')

        # Split text into sentences for better prosody - based on OpenVoice approach
        import re
        # More careful sentence splitting to avoid breaking short phrases
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # If no splitting occurred or text is short, treat as single sentence
        if not sentences or len(sentences) == 1 and len(text.strip()) < 100:
            sentences = [text.strip()]  # fallback to original text
            
        logger.info(f'[VoiceSynth] Processing {len(sentences)} sentence(s): {sentences}')
        
        # Get reference embedding once for all sentences - try improved method first
        g_latent = None
        if reference_audio:
            g_latent = self._extract_reference_embedding_improved(reference_audio)
            if g_latent is None:
                logger.debug("[VoiceSynth] Falling back to basic reference embedding")
                g_latent = self._extract_reference_embedding(reference_audio)
        
        # Speaker / style conditioning setup
        speakers_map = self.config.get('speakers', {}) if isinstance(self.config, dict) else {}
        spk_id = speakers_map.get(style, speakers_map.get('default', 0))
        if g_latent is None and reference_audio and hasattr(self.model, 'emb_g'):
            try:
                n_spk = self.model.emb_g.num_embeddings
                h = int(hashlib.md5(reference_audio.encode('utf-8')).hexdigest(), 16)
                spk_id = h % n_spk
            except Exception:
                pass
        if hasattr(self.model, 'emb_g'):
            n_total = self.model.emb_g.num_embeddings
            if spk_id >= n_total:
                spk_id = 0
        sid = torch.LongTensor([spk_id]).to(self.device)

        # Process each sentence
        audio_segments = []
        sampling_rate = self.config.get('sampling_rate', 22050)
        
        for i, sentence in enumerate(sentences):
            # 1. Text -> ids
            seq = self._text_to_ids(sentence, language=language, force_chars=False)
            logger.info(f'[VoiceSynth] Sentence {i+1}: "{sentence}" -> {len(seq)} tokens: {seq[:20]}{"..." if len(seq) > 20 else ""}')
            if seq and self.enable_prosody_heuristics:
                vowel_chars = set('aeiou')
                decoded = ''.join([self.symbols[j] if j < len(self.symbols) else '' for j in seq])
                vowels = sum(1 for c in decoded if c in vowel_chars)
                ratio = vowels / max(1, len(decoded))
                sentence_length_scale = length_scale
                if ratio < 0.25:
                    sentence_length_scale *= 1.06
                elif ratio > 0.5:
                    sentence_length_scale *= 0.97
                if len(seq) < 12:
                    sentence_length_scale *= 1.04
            else:
                sentence_length_scale = length_scale
                
            vocab_size = int(self.model.enc_p.emb.num_embeddings)
            before = len(seq)
            seq = [j for j in seq if 0 <= j < vocab_size]
            if len(seq) != before:
                logger.debug('[VoiceSynth] Filtered %d invalid token ids', before - len(seq))
            if not seq:
                logger.warning(f'Empty sequence after tokenization for sentence: "{sentence}"')
                # Try fallback with character-level processing
                fallback_seq = self._text_to_ids(sentence, language=language, force_chars=True)
                if fallback_seq:
                    logger.info(f'[VoiceSynth] Using character fallback for: "{sentence}" -> {len(fallback_seq)} chars')
                    seq = fallback_seq
                else:
                    continue

            logger.debug('[VoiceSynth] Sentence %d: "%s" -> ids=%s', i+1, sentence, seq[:60])
            x = torch.LongTensor(seq).unsqueeze(0).to(self.device)
            x_lengths = torch.LongTensor([x.shape[-1]]).to(self.device)

            # 2. Inference with improved parameters based on OpenVoice
            with torch.no_grad():
                duration_bias = None
                if self.enable_prosody_heuristics:
                    try:
                        puncts = {',', '.', '!', '?'}
                        toks = [self.symbols[j] if j < len(self.symbols) else '' for j in seq]
                        bias = torch.zeros(1, 1, len(seq), device=self.device)
                        for idx, tk in enumerate(toks):
                            if tk in puncts and idx > 0:
                                # extend previous token (pause emphasis)
                                bias[0, 0, idx-1] += 0.20  # Increased for better pauses
                            elif tk in 'aeiou':
                                # Always elongate vowels slightly
                                base = 0.08  # Increased base elongation
                                if hasattr(self, '_last_stress_indices') and idx in getattr(self, '_last_stress_indices', set()):
                                    base += 0.12  # More stress elongation
                                # If next is punctuation add a bit more
                                if idx+1 < len(toks) and toks[idx+1] in puncts:
                                    base += 0.06
                                bias[0, 0, idx] += base
                            # Encourage completion by slightly extending all tokens toward the end
                            if idx >= len(toks) * 0.6:  # Last 40% of tokens
                                bias[0, 0, idx] += 0.05
                        if sentence.strip().endswith('?'):
                            for ridx in range(len(toks)-1, -1, -1):
                                if toks[ridx] in 'aeiou':
                                    bias[0, 0, ridx] += 0.15  # Increased question intonation
                                    break
                        duration_bias = bias
                    except Exception:
                        pass
                        
                # Use OpenVoice-style parameters for better quality and prosody
                if self.clarity_mode:
                    infer_kwargs = dict(sid=sid, length_scale=sentence_length_scale, 
                                      noise_scale=0.55, noise_scale_w=0.5, sdp_ratio=0.25)
                else:
                    # OpenVoice uses noise_scale=0.667, noise_scale_w=0.8 for final synthesis
                    # For better prosody, use slightly higher length_scale and adjusted noise
                    infer_kwargs = dict(sid=sid, length_scale=sentence_length_scale * 1.05, 
                                      noise_scale=0.667, noise_scale_w=0.9, sdp_ratio=0.2)
                if duration_bias is not None:
                    infer_kwargs['duration_bias'] = duration_bias
                if g_latent is not None:
                    infer_kwargs['g_latent'] = g_latent
                    
                y_hat, attn, y_mask, meta = self.model.infer(x, x_lengths, **infer_kwargs)
                
                try:  # optional light duration smoothing - be more conservative to avoid truncation
                    dur = attn.squeeze(1).sum(2).squeeze(0).cpu().numpy()
                    if dur.size > 3:
                        import numpy as _np
                        median_dur = _np.median(dur)
                        logger.debug(f"[VoiceSynth] Median duration: {median_dur}, length_scale: {sentence_length_scale}")
                        # Only adjust if duration is very short and we haven't already increased length_scale significantly
                        if median_dur < 1.0 and sentence_length_scale < 1.5:
                            new_scale = sentence_length_scale * 1.15
                            logger.debug(f"[VoiceSynth] Adjusting length_scale to {new_scale} for better completion")
                            infer_kwargs['length_scale'] = new_scale
                            y_hat, _, _, _ = self.model.infer(x, x_lengths, **infer_kwargs)
                except Exception as e:
                    logger.debug(f"[VoiceSynth] Duration smoothing failed: {e}")
                    pass
                    
                audio_segment = y_hat[0, 0].data.cpu().numpy()
                
            # 3. Post-processing for this segment
            if self.clarity_mode and audio_segment.size > 0:
                audio_segment = audio_segment - audio_segment.mean()
                peak = np.max(np.abs(audio_segment)) + 1e-9
                if peak > 0:
                    audio_segment = 0.89 * audio_segment / peak
                rms = np.sqrt(np.mean(audio_segment**2) + 1e-9)
                target_rms = 0.08
                if rms < target_rms * 0.9:
                    audio_segment *= (target_rms / max(rms, 1e-6))
                preemph = 0.97
                audio_segment = np.append(audio_segment[0], audio_segment[1:] - preemph * audio_segment[:-1])
            
            audio_segments.append(audio_segment)
            
            # Add pause between sentences (50ms like OpenVoice)
            if i < len(sentences) - 1:
                pause_samples = int(0.05 * sampling_rate)  # 50ms pause
                pause = np.zeros(pause_samples)
                audio_segments.append(pause)
        
        # Concatenate all segments
        if audio_segments:
            final_audio = np.concatenate(audio_segments)
        else:
            logger.error('No audio segments generated')
            return False
            
        # Final normalization
        if final_audio.size > 0:
            # Remove DC bias
            final_audio = final_audio - final_audio.mean()
            # Normalize to prevent clipping
            peak = np.max(np.abs(final_audio))
            if peak > 0.95:
                final_audio = final_audio * 0.95 / peak

        sf.write(output_path, final_audio, sampling_rate)
        return os.path.exists(output_path)
