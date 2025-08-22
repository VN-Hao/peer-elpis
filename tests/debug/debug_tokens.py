#!/usr/bin/env python3

import sys
import os
# Add project root to path (go up two levels from tests/debug/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from voice.modules.voice_synth import VoiceSynthesizer

def debug_tokenization():
    print("=== Tokenization Debug ===")
    
    synth = VoiceSynthesizer()
    
    test_cases = ["Hello", "there", "Hello there", "Hello there."]
    
    for text in test_cases:
        print(f"\nTesting: '{text}'")
        try:
            seq = synth._text_to_ids(text)
            print(f"  Raw sequence: {seq}")
            print(f"  Length: {len(seq)}")
            
            if hasattr(synth, 'symbols') and synth.symbols:
                symbols = []
                for i in seq:
                    if i < len(synth.symbols):
                        symbols.append(synth.symbols[i])
                    else:
                        symbols.append(f"?{i}")
                print(f"  Symbols: {symbols}")
                print(f"  Text: {''.join(symbols)}")
            else:
                print("  No symbols available")
                
        except Exception as e:
            print(f"  ERROR: {e}")

if __name__ == '__main__':
    debug_tokenization()
