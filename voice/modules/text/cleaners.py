"""Text cleaning utilities."""

import re

def cjke_cleaners2(text):
    """Basic text cleaner for CJK and English."""
    text = text.lower()
    text = re.sub(r'[^a-z\u4e00-\u9fff]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def english_cleaners(text):
    """Pipeline for English text."""
    text = text.lower()
    text = re.sub(r'[^a-z]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
