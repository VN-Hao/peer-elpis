#!/usr/bin/env python3
"""
Simple test for voice synthesis debugging
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("Starting simple voice test...")

try:
    from voice.modules.voice_synth import VoiceSynthesizer
    print("✅ Import successful")
    
    synth = VoiceSynthesizer("checkpoints/converter/checkpoint.pth")
    print("✅ Initialization successful")
    
    # Test tokenization first
    tokens = synth._text_to_ids("Hello")
    print(f"✅ Tokenization: 'Hello' -> {tokens}")
    
    # Test basic synthesis
    audio, sr = synth.synthesize_audio("Hello", length_scale=1.0)
    print(f"✅ Synthesis successful: {len(audio)} samples at {sr} Hz")
    
    # Save output
    import soundfile as sf
    sf.write("simple_test.wav", audio, sr)
    print("✅ Saved to simple_test.wav")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("Test complete!")
