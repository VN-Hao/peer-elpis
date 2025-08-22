#!/usr/bin/env python3
"""
Quick test to verify voice synthesis quality improvements are working.
"""
import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from voice.modules.voice_synth import VoiceSynthesizer

def test_voice_quality():
    """Test the enhanced voice synthesis with improved tokenization."""
    print("=== Voice Quality Test ===")
    
    # Initialize synthesizer
    model_path = "checkpoints/converter/checkpoint.pth"
    config_path = "checkpoints/converter/config.json"
    
    if not os.path.exists(model_path):
        print(f"❌ Model not found: {model_path}")
        return
    
    if not os.path.exists(config_path):
        print(f"❌ Config not found: {config_path}")
        return
    
    print("✅ Initializing VoiceSynthesizer...")
    synth = VoiceSynthesizer(model_path=model_path)
    
    # Test phrases that were problematic before
    test_phrases = [
        "Hello there.",
        "This is a test of voice quality.",
        "Nice to meet you.",
        "The quick brown fox jumps over the lazy dog."
    ]
    
    reference_audio = "assets/sample_voice/firefly_voice_compact.mp3"
    if not os.path.exists(reference_audio):
        print(f"⚠️  Reference audio not found: {reference_audio}")
        print("   Using enhanced pseudo embedding...")
        reference_audio = None
    
    for i, text in enumerate(test_phrases):
        print(f"\n🎵 Testing: '{text}'")
        
        try:
            # Test tokenization first
            print("   Checking tokenization...")
            tokens = synth._text_to_ids(text)
            print(f"   Tokens ({len(tokens)}): {tokens[:20]}{'...' if len(tokens) > 20 else ''}")
            
            # Test synthesis
            print("   Synthesizing audio...")
            start_time = time.time()
            
            audio, sr = synth.synthesize_audio(
                text, 
                reference_audio=reference_audio,
                noise_scale=0.667,
                noise_scale_w=0.9,
                length_scale=1.0
            )
            
            duration = time.time() - start_time
            audio_length = len(audio) / sr
            
            print(f"   ✅ Success! Audio: {audio_length:.2f}s, Processing: {duration:.2f}s")
            
            # Save test output
            output_file = f"test_output_{i+1}.wav"
            import soundfile as sf
            sf.write(output_file, audio, sr)
            print(f"   💾 Saved: {output_file}")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n=== Test Complete ===")
    print("Play the generated test_output_*.wav files to verify quality")

if __name__ == "__main__":
    test_voice_quality()
