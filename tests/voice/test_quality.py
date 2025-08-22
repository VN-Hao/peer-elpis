#!/usr/bin/env python3

import sys
import os
# Add project root to path (go up two levels from tests/voice/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from voice.tts_engine import TTSEngine
import glob

def test_synthesis():
    # Find reference audio
    ref_files = glob.glob('assets/sample_voice/*.mp3')
    if not ref_files:
        ref_files = glob.glob('assets/sample_voice/*.wav')
    
    if not ref_files:
        print("No reference audio found")
        return
        
    ref = ref_files[0]
    print(f"Using reference: {ref}")
    
    engine = TTSEngine()
    engine.set_voice_reference(ref)
    
    if not engine._is_openvoice_available():
        print("OpenVoice not available")
        return
    
    # Test cases to address user's issues
    test_cases = [
        ("Hello there.", "tests/quality_test_hello_there.wav"),
        ("Hello", "tests/quality_test_hello_only.wav"),
        ("There", "tests/quality_test_there_only.wav"), 
        ("Hi there, how are you?", "tests/quality_test_longer.wav"),
        ("Nice to meet you.", "tests/quality_test_nice.wav")
    ]
    
    print("Testing synthesis quality...")
    for text, output in test_cases:
        print(f"\nSynthesizing: '{text}'")
        try:
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output), exist_ok=True)
            
            # Use synthesize_audio method that returns audio data
            audio, sr = engine.openvoice.synthesize_audio(
                text=text,
                reference_audio=ref,
                speaker='default',
                language='English',
                speed=1.0
            )
            
            # Save the audio
            import soundfile as sf
            sf.write(output, audio, sr)
            
            if os.path.exists(output):
                size_kb = os.path.getsize(output) / 1024
                print(f"  ✓ Success: {output} ({size_kb:.1f} KB)")
            else:
                print(f"  ✗ Failed to save: {output}")
                
        except Exception as e:
            print(f"  ✗ Failed: {e}")

if __name__ == '__main__':
    test_synthesis()
