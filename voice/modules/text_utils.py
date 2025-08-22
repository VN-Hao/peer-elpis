"""
Text processing utilities for OpenVoice implementation.
"""

import re
from typing import List

# IPA (International Phonetic Alphabet) symbols
_pad = '_'
_punctuation = ';:,.!?¡¿—…"«»"" '
_letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
_letters_ipa = "ɑɐɒæɓʙβɔɕçɗɖðʤəɘɚɛɜɝɞɟʄɡɠɢʛɦɧħɥʜɨɪʝɭɬɫɮʟɱɯɰŋɳɲɴøɵɸθœɶʘɹɺɾɻʀʁɽʂʃʈʧʉʊʋⱱʌɣɤʍχʎʏʑʐʒʔʡʕʢǀǁǂǃˈˌːˑʼʴʰʱʲʷˠˤ˞↓↑→↗↘'̩'ᵻ"

# Regular expression matching whitespace:
_whitespace_re = re.compile(r'\s+')

# Regular expression matching Japanese without punctuation marks:
_japanese_marks = '？！。，'
_japanese_characters = re.compile(r'[A-Za-z\d\u3005\u3040-\u30ff\u4e00-\u9fff\uff11-\uff19\uff21-\uff3a\uff41-\uff5a\uff66-\uff9d]')

# List of symbols for phonetic representation
symbols = [_pad] + list(_punctuation) + list(_letters) + list(_letters_ipa)

# Dictionary mapping symbols to integer indices
_symbol_to_id = {s: i for i, s in enumerate(symbols)}
_id_to_symbol = {i: s for i, s in enumerate(symbols)}


def text_to_sequence(text: str) -> List[int]:
    """Convert text string to sequence of symbol IDs."""
    sequence = []
    for symbol in text:
        if symbol in _symbol_to_id:
            sequence.append(_symbol_to_id[symbol])
    return sequence


def sequence_to_text(sequence: List[int]) -> str:
    """Convert sequence of symbol IDs to text string."""
    result = []
    for symbol_id in sequence:
        if symbol_id in _id_to_symbol:
            result.append(_id_to_symbol[symbol_id])
    return ''.join(result)


def clean_text(text: str, language: str = 'en') -> str:
    """Perform text cleaning and normalization."""
    text = text.strip()
    
    if language == 'ja':
        # For Japanese, keep only valid characters
        text = ''.join(char for char in text if _japanese_characters.match(char) or char in _japanese_marks)
    else:
        # For other languages, normalize whitespace
        text = re.sub(_whitespace_re, ' ', text)
    
    return text
