"""Text processing utilities."""

import re
from typing import List

from .symbols import symbols

# Symbol mappings
_symbol_to_id = {s: i for i, s in enumerate(symbols)}
_id_to_symbol = {i: s for i, s in enumerate(symbols)}

def text_to_sequence(text: str, cleaner_names: List[str]) -> List[int]:
    """Convert text string to sequence of symbol ids.
    
    Args:
        text: Input text
        cleaner_names: List of cleaner names to apply
        
    Returns:
        List of symbol ids
    """
    sequence = []
    clean_text = _clean_text(text, cleaner_names)
    for symbol in clean_text:
        if symbol in _symbol_to_id:
            sequence.append(_symbol_to_id[symbol])
    return sequence

def cleaned_text_to_sequence(cleaned_text: str) -> List[int]:
    """Convert pre-cleaned text to sequence of symbol ids."""
    sequence = []
    for symbol in cleaned_text:
        if symbol in _symbol_to_id:
            sequence.append(_symbol_to_id[symbol])
    return sequence

def sequence_to_text(sequence: List[int]) -> str:
    """Convert sequence of symbol ids back to text."""
    result = []
    for symbol_id in sequence:
        if symbol_id in _id_to_symbol:
            result.append(_id_to_symbol[symbol_id])
    return ''.join(result)

def _clean_text(text: str, cleaner_names: List[str]) -> str:
    """Run series of cleaners on text."""
    from . import cleaners
    for name in cleaner_names:
        if name == 'cjke_cleaners2':
            text = cleaners.cjke_cleaners2(text)
        elif name == 'english_cleaners':
            text = cleaners.english_cleaners(text)
        else:
            raise Exception(f'Unknown cleaner: {name}')
    return text
