#!/usr/bin/env python3

import sys
import os
# Add project root to path (go up two levels from tests/debug/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from voice.modules.voice_synth import VoiceSynthesizer

def check_r_symbols():
    synth = VoiceSynthesizer()
    
    # Check if 'r' exists in different forms
    r_variants = ['r', 'ɹ', 'ɾ', 'ʁ']
    print('Checking r-sound variants:')
    for r_var in r_variants:
        if r_var in synth.sym2id:
            print(f'  {r_var} -> token {synth.sym2id[r_var]}')
        else:
            print(f'  {r_var} -> NOT FOUND')
    
    # Check what token 99 actually maps to
    if 99 < len(synth.symbols):
        print(f'Token 99 -> symbol: "{synth.symbols[99]}"')
    else:
        print(f'Token 99 -> OUT OF RANGE (max: {len(synth.symbols)-1})')
    
    print(f'Total symbols: {len(synth.symbols)}')
    
    # Also check if we have common ASCII 'r'
    if 'r' in synth.sym2id:
        print(f'ASCII r -> token {synth.sym2id["r"]}')
    else:
        # See what we have that looks like r
        r_like = [s for s in synth.symbols if 'r' in s.lower()]
        print(f'r-like symbols: {r_like}')

if __name__ == '__main__':
    check_r_symbols()
