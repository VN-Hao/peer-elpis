import os
import sys
import argparse
import logging

# Ensure project root on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from voice.tts_engine import TTSEngine

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


def run(reference_audio: str, text: str, output: str):
    if not os.path.isfile(reference_audio):
        raise SystemExit(f'Reference audio not found: {reference_audio}')
    engine = TTSEngine()
    engine.set_voice_reference(reference_audio)
    # Directly access internal openvoice synth API to control output path
    if not engine._is_openvoice_available():
        raise SystemExit('OpenVoice backend not available (torch missing or checkpoint not found).')

    # Use internal synthesizer to produce output synchronously
    synth = engine.openvoice
    ok = synth.synthesize(text=text, reference_audio=reference_audio, output_path=output)
    if not ok:
        raise SystemExit('Synthesis failed')
    if not os.path.exists(output):
        raise SystemExit('Output file not created')
    size_kb = os.path.getsize(output)/1024.0
    print(f'Generated: {output} ({size_kb:.1f} KB)')


def main():
    parser = argparse.ArgumentParser(description='Test voice cloning synthesis')
    parser.add_argument('--ref', required=True, help='Path to reference wav/mp3')
    parser.add_argument('--text', default='Hello, this is a cloned test voice.')
    parser.add_argument('--out', default='clone_test_output.wav')
    args = parser.parse_args()
    run(args.ref, args.text, args.out)


if __name__ == '__main__':
    main()
