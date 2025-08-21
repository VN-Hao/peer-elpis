import os
import sys
import torch
import numpy as np
import logging
from openvoice.api import BaseSpeakerTTS, ToneColorConverter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def synthesize_speech(text, output_path, engine_dir):
    """Synthesize speech using OpenVoice with a given engine directory."""
    # Ensure text is unicode and only contains ASCII characters
    if not isinstance(text, str):
        text = str(text, 'utf-8', errors='replace')
    # Replace any non-ASCII characters with their closest ASCII equivalent
    text = text.encode('ascii', 'replace').decode('ascii')
    logger.info(f"Starting synthesis with text: {text}")
    logger.info(f"Output path: {output_path}")
    logger.info(f"Engine directory: {engine_dir}")
    
    # Validate engine directory
    if not os.path.exists(engine_dir):
        raise RuntimeError(f"Engine directory not found: {engine_dir}")
    if not os.path.exists(os.path.join(engine_dir, 'se.pth')):
        raise RuntimeError(f"Speaker embedding file not found in engine directory: {engine_dir}/se.pth")
        
    # Debug: Check the speaker embedding file format
    se_data = torch.load(os.path.join(engine_dir, 'se.pth'))
    if isinstance(se_data, dict):
        logger.info(f"Speaker embedding is a dictionary with keys: {list(se_data.keys())}")
        for key, value in se_data.items():
            if isinstance(value, torch.Tensor):
                logger.info(f"Key '{key}' contains tensor of shape: {value.shape}")
    else:
        logger.info(f"Speaker embedding is of type: {type(se_data)}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Get paths
    openvoice_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'OpenVoice-main'))
    ckpt_base = os.path.join(openvoice_root, 'checkpoints', 'base_speakers', 'EN')
    ckpt_converter = os.path.join(openvoice_root, 'checkpoints', 'converter')
    
    logger.info(f"Using OpenVoice root: {openvoice_root}")
    
    # Set device
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")
    
    # Initialize models
    logger.info("Initializing models...")
    base_speaker_tts = BaseSpeakerTTS(os.path.join(ckpt_base, 'config.json'), device=device)
    base_speaker_tts.load_ckpt(os.path.join(ckpt_base, 'checkpoint.pth'))
    
    tone_color_converter = ToneColorConverter(os.path.join(ckpt_converter, 'config.json'), device=device)
    tone_color_converter.load_ckpt(os.path.join(ckpt_converter, 'checkpoint.pth'))
    
    # Load target speaker embedding
    target_se_path = os.path.join(engine_dir, 'se.pth')
    if not os.path.exists(target_se_path):
        raise RuntimeError(f"Speaker embedding not found at {target_se_path}")
    
    logger.info("Loading speaker embeddings...")
    target_se = torch.load(target_se_path)
    if isinstance(target_se, dict):
        target_se = target_se['speaker_embedding']
    
    # Load source speaker embedding
    source_se_path = os.path.join(ckpt_base, 'en_default_se.pth')
    logger.info(f"Loading source speaker embedding from: {source_se_path}")
    source_se = torch.load(source_se_path).to(device)
    
    # Load target speaker embedding from engine directory
    target_se_path = os.path.join(engine_dir, 'se.pth')
    logger.info(f"Loading target speaker embedding from: {target_se_path}")
    target_se_data = torch.load(target_se_path)
    
    # Handle different speaker embedding formats
    if isinstance(target_se_data, dict):
        if 'speaker_embedding' in target_se_data:
            target_se = target_se_data['speaker_embedding'].to(device)
        elif 'se' in target_se_data:
            target_se = target_se_data['se'].to(device)
        elif len(target_se_data) == 1:
            # If there's only one key in the dict, use its value
            target_se = next(iter(target_se_data.values())).to(device)
        else:
            logger.error(f"Speaker embedding format unknown. Keys found: {list(target_se_data.keys())}")
            raise ValueError("Could not find speaker embedding in the saved data")
    else:
        target_se = target_se_data.to(device)
    
    logger.info("Speaker embeddings loaded successfully")
    
    # Create a temporary file for intermediate output
    temp_base_output = os.path.join(os.path.dirname(output_path), 'base_output.wav')
    
    # Generate speech
    logger.info("Generating base speech...")
    base_speaker_tts.tts(
        text=text,
        output_path=temp_base_output,
        speaker='default',  # Use default speaker for base audio
        language='English'
    )
    
    # Read the generated audio file
    logger.info("Loading generated base speech...")
    import soundfile as sf
    audio, sample_rate = sf.read(temp_base_output)
    
    logger.info("Converting voice...")
    # Save intermediate audio to a temporary file for conversion
    temp_convert_input = os.path.join(os.path.dirname(output_path), 'convert_input.wav')
    sf.write(temp_convert_input, audio, sample_rate)
    
    try:
        if hasattr(tone_color_converter, 'convert'):
            converted_audio = tone_color_converter.convert(temp_convert_input, source_se, target_se, output_path=None)
        elif hasattr(tone_color_converter, 'inference'):
            converted_audio = tone_color_converter.inference(temp_convert_input, source_se, target_se, output_path=None)
        elif hasattr(tone_color_converter, '__call__'):
            converted_audio = tone_color_converter(temp_convert_input, source_se, target_se, output_path=None)
        else:
            methods = [method for method in dir(tone_color_converter) if not method.startswith('_')]
            logger.error(f"Available methods: {methods}")
            raise RuntimeError(f"No suitable conversion method found. Available methods: {methods}")
    finally:
        # Clean up the temporary input file
        try:
            os.remove(temp_convert_input)
        except:
            pass
            
    # Ensure we have numpy array output
    if isinstance(converted_audio, torch.Tensor):
        converted_audio = converted_audio.cpu().numpy()
    if converted_audio.dtype != np.float32:
        converted_audio = converted_audio.astype(np.float32)
    
    # Save the converted audio
    logger.info(f"Saving audio to: {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        if hasattr(tone_color_converter, 'hps'):
            # Use the converter's native sample rate if available
            sample_rate = tone_color_converter.hps.data.sampling_rate
        import soundfile as sf
        sf.write(output_path, converted_audio, sample_rate)
        
        # Verify the file was created
        if os.path.exists(output_path):
            logger.info(f"Successfully saved audio file ({os.path.getsize(output_path)} bytes)")
        else:
            raise RuntimeError("Failed to create output audio file")
            
    finally:
        # Clean up temporary files
        try:
            if os.path.exists(temp_base_output):
                os.remove(temp_base_output)
        except Exception as e:
            logger.warning(f"Failed to clean up temporary files: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python openvoice_engine.py <text> <output_path> <engine_dir>")
        sys.exit(1)
        
    text = sys.argv[1]
    output_path = sys.argv[2]
    engine_dir = sys.argv[3]
    
    try:
        synthesize_speech(text, output_path, engine_dir)
    except Exception as e:
        logger.exception("Synthesis failed")
        sys.exit(1)
