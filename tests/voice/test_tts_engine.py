#!/usr/bin/env python3

"""
Test script for TTSEngine integration.
"""

import os
import sys

def test_tts_engine():
    """Test TTS engine initialization and basic functionality."""
    try:
        print("=== TTS Engine Test ===")
        
        print("✅ Importing TTS Engine...")
        from voice.tts_engine import TTSEngine
        
        print("✅ Creating TTS Engine...")
        engine = TTSEngine()
        
        print("✅ Testing speak method...")
        test_text = "Hello there, this is a test of the new OpenVoice integration."
        engine.speak(test_text, callback=lambda: print("Speaking..."))
        
        print("✅ TTS Engine test completed successfully!")
        
    except Exception as e:
        print(f"❌ TTS Engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    return True

if __name__ == "__main__":
    success = test_tts_engine()
    sys.exit(0 if success else 1)
