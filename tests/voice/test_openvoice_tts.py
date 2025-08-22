#!/usr/bin/env python3
"""
Test the proper two-stage OpenVoice TTS implementation.
This should produce clean audio without noise.
"""
import os
import sys
# Add project root to path (go up two levels from tests/voice/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from voice.openvoice_tts import OpenVoiceTTS
import soundfile as sf

def test_openvoice_tts():
    """Test the OpenVoice TTS implementation."""
    print("=== OpenVoice TTS Test ===")
    
    try:
        # Initialize OpenVoice TTS
        print("✅ Initializing OpenVoice TTS...")
        tts = OpenVoiceTTS()
        
        # Test phrases
        test_phrases = [
            "Hello there.",
            "This is a test of voice quality using OpenVoice.",
            "The quick brown fox jumps over the lazy dog."
        ]
        
        # Reference audio for voice cloning
        reference_audio = "assets/sample_voice/firefly_voice_compact.mp3"
        use_reference = os.path.exists(reference_audio)
        
        if use_reference:
            print(f"✅ Using reference audio: {reference_audio}")
        else:
            print("⚠️  No reference audio found, using base speaker voice")
        
        for i, text in enumerate(test_phrases):
            print(f"\n🎵 Testing: '{text}'")
            
            try:
                # Test synthesis
                print("   Synthesizing with OpenVoice...")
                
                audio, sr = tts.synthesize_audio(
                    text,
                    reference_audio=reference_audio if use_reference else None,
                    speaker='default',
                    language='English',
                    speed=1.0
                )
                
                print(f"   ✅ Success! Audio: {len(audio)/sr:.2f}s at {sr} Hz")
                
                # Save output
                output_file = f"openvoice_output_{i+1}.wav"
                sf.write(output_file, audio, sr)
                print(f"   💾 Saved: {output_file}")
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n=== Test Complete ===")
        print("Check the openvoice_output_*.wav files - they should be clean without noise!")
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_openvoice_tts()
