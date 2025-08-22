import os, sys, glob, argparse, logging
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from voice.tts_engine import TTSEngine

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def find_sample_voice():
    base = os.path.join(ROOT, 'assets', 'sample_voice')
    if not os.path.isdir(base):
        return None
    for ext in ('*.wav','*.mp3','*.flac','*.ogg'):
        matches = glob.glob(os.path.join(base, ext))
        if matches:
            return matches[0]
    return None

def main():
    parser = argparse.ArgumentParser(description='Run sample voice cloning synthesis test')
    parser.add_argument('--text', default='Hello, this is a cloned sample voice test.')
    parser.add_argument('--out', default='sample_clone_output.wav')
    parser.add_argument('--ref', default=None, help='Optional override reference path')
    args = parser.parse_args()

    ref = args.ref or find_sample_voice()
    if not ref:
        raise SystemExit('No sample voice file found in assets/sample_voice. Place a wav/mp3 there or pass --ref.')
    if not os.path.isfile(ref):
        raise SystemExit(f'Reference file not found: {ref}')

    print(f'Using reference: {ref}')
    engine = TTSEngine()
    engine.set_voice_reference(ref)
    if not engine._is_openvoice_available():
        raise SystemExit('OpenVoice backend not available (torch or checkpoint missing).')

    out_path = os.path.abspath(args.out)
    ok = engine.openvoice.synthesize(text=args.text, reference_audio=ref, output_path=out_path)
    if not ok or not os.path.exists(out_path):
        raise SystemExit('Synthesis failed or output not created')
    print(f'Output written: {out_path} ({os.path.getsize(out_path)/1024:.1f} KB)')

if __name__ == '__main__':
    main()
