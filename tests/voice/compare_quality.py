#!/usr/bin/env python3
"""
Compare audio quality: base speaker vs reference audio
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from voice.openvoice_tts import OpenVoiceTTS
import soundfile as sf

def compare_quality():
    """Compare base speaker vs reference audio quality."""
    print("=== Audio Quality Comparison ===")
    
    try:
        tts = OpenVoiceTTS()
        test_text = "Hello there, this is a voice quality comparison test."
        
        # Test 1: Base speaker (cleanest)
        print("\n🎵 Generating with BASE SPEAKER (cleanest)...")
        audio1, sr1 = tts.synthesize_audio(
            test_text,
            reference_audio=None,
            speaker='default',
            language='English',
            speed=1.0
        )
        sf.write("base_speaker_clean.wav", audio1, sr1)
        print("   ✅ Saved: base_speaker_clean.wav")
        
        # Test 2: With reference audio (voice cloning)
        reference_audio = "assets/sample_voice/firefly_voice_compact.mp3"
        if os.path.exists(reference_audio):
            print(f"\n🎵 Generating with REFERENCE AUDIO...")
            audio2, sr2 = tts.synthesize_audio(
                test_text,
                reference_audio=reference_audio,
                speaker='default',
                language='English',
                speed=1.0
            )
            sf.write("reference_voice_clone.wav", audio2, sr2)
            print("   ✅ Saved: reference_voice_clone.wav")
        
        print("\n=== Comparison Complete ===")
        print("🔊 Listen to both files:")
        print("📁 base_speaker_clean.wav - Clean default voice (no cloning)")
        print("📁 reference_voice_clone.wav - Cloned voice (may inherit reference noise)")
        print("\n💡 The base speaker should be cleaner. Any noise in the cloned version")
        print("   comes from the reference audio quality.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    compare_quality()
