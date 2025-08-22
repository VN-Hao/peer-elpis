#!/usr/bin/env python3

import sys
import os
import logging
# Add project root to path (go up two levels from tests/debug/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

from voice.tts_engine import TTSEngine

def main():
    print("=== TTS Engine Tokenization Debug ===")
    
    engine = TTSEngine()
    
    if not engine._is_openvoice_available():
        print("OpenVoice not available, using fallback")
        return
    
    test_text = "Hello there."
    print(f"Testing text: '{test_text}'")
    
    # Simple test - show engine capabilities
    try:
        print("OpenVoice TTS engine is available and ready")
        print("Text processing capabilities:")
        print("  - Two-stage synthesis (BaseSpeaker + ToneConverter)")
        print("  - IPA phoneme processing")
        print("  - Multi-language support")
        
        # Test basic text analysis
        test_cases = [
            "Hello",
            "there", 
            "Hello there",
            "Hello there.",
            "Hi there!",
            "How are you?"
        ]
        
        print("\nAnalyzing test cases:")
        for i, text in enumerate(test_cases, 1):
            print(f"{i}. '{text}'")
            print(f"   - Length: {len(text)} chars")
            print(f"   - Words: {len(text.split())} words")
            # Show character composition
            alpha_chars = sum(c.isalpha() for c in text)
            punct_chars = sum(not c.isalnum() and not c.isspace() for c in text)
            print(f"   - Alpha: {alpha_chars}, Punct: {punct_chars}")
            
    except Exception as e:
        print(f"Error during analysis: {e}")

if __name__ == '__main__':
    main()
