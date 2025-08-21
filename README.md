# Peer Elpis - AI Assistant with Voice Cloning

An AI assistant application that combines chat functionality with voice cloning capabilities, featuring a Live2D avatar for an interactive experience.

## Features

- 💬 Interactive Chat Interface
- 🎙️ Voice Cloning using OpenVoice
- 👤 Live2D Avatar Animation
- 🔊 Text-to-Speech with Voice Customization
- 🎭 Customizable Avatar Expression
- 🖥️ Modern PyQt5-based UI

## Prerequisites

- Python 3.10 or higher
- PyQt5
- CUDA-capable GPU (optional, for faster voice processing)
- Windows OS (currently optimized for Windows)

## Installation

1. Clone the repository with submodules:
```bash
# Clone the main repository
git clone https://github.com/VN-Hao/peer-elpis.git
cd peer-elpis

# Initialize and update the OpenVoice submodule
git submodule update --init --recursive
```

2. Create and activate the main virtual environment:
```bash
# Create and activate main environment
python -m venv env
.\env\Scripts\activate  # On Windows
source env/bin/activate  # On Linux/Mac

# Install main project dependencies
pip install -r requirements.txt
```

3. Set up OpenVoice environment (for voice cloning):
```bash
# Create and activate OpenVoice environment
python -m venv env_ov
.\env_ov\Scripts\activate  # On Windows
source env_ov/bin/activate  # On Linux/Mac

# Install OpenVoice dependencies
cd OpenVoice-main
pip install -r requirements.txt
```

4. Download required models:
```bash
# Create directories for models
mkdir -p OpenVoice-main/checkpoints/base_speakers/EN

# Download base models from OpenVoice releases
# Place the following files in OpenVoice-main/checkpoints/base_speakers/EN/:
# - config.json
# - model.pth
# - en_default_se.pth
```

## Configuration

1. OpenVoice Setup:
   - Download the required models from [OpenVoice Releases](https://github.com/myshell-ai/OpenVoice/releases)
   - Required files for `OpenVoice-main/checkpoints/base_speakers/EN/`:
     * `config.json` - Model configuration
     * `model.pth` - Base speaker model
     * `en_default_se.pth` - English speaker embeddings
   - Optional: Download converter model files to `OpenVoice-main/checkpoints/converter/`

2. Avatar Setup:
   - The default Live2D avatar is included in `assets/avatar/`
   - Custom avatars can be added to the same directory
   - Required files structure:
     ```
     assets/
     └── avatar/
         ├── cubism4.min.js
         ├── index.html
         ├── live2dcubismcore.js
         └── ANIYA/            # Default avatar
             └── model files...
     ```

## Usage

1. Start the application:
```bash
python main.py
```

2. First-time Setup:
   - The application will prompt you to set up your voice preference
   - You can either:
     - Record a reference audio for voice cloning
     - Select from pre-exported voice engines
     - Use default text-to-speech

3. Chat Interface:
   - Type messages in the input field
   - The AI will respond with both text and voice
   - The Live2D avatar will animate during speech

4. Voice Controls:
   - Adjust volume using the slider
   - Mute/unmute with the speaker icon
   - Change voice settings through the configuration panel

## Project Structure

- `main.py` - Application entry point
- `bot/` - AI chat bot implementation
- `voice/` - Voice synthesis and processing
- `ui/` - User interface components
- `services/` - Core services (TTS, LLM, etc.)
- `controllers/` - Application logic
- `assets/` - Avatar and static resources

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## Troubleshooting

Common issues and solutions:

1. Voice synthesis not working:
   - Ensure OpenVoice models are correctly installed
   - Check Python version compatibility
   - Verify CUDA setup if using GPU

2. Avatar not displaying:
   - Check WebView2 installation
   - Verify avatar assets are present
   - Check browser console for errors

3. Chat not responding:
   - Verify network connection
   - Check LLM service configuration
   - Ensure proper API keys are set

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

### Technologies and Frameworks
- [OpenVoice](https://github.com/myshell-ai/OpenVoice) for voice cloning technology
- Live2D for avatar animation framework
- PyQt team for the UI framework

### AI Development Assistance
This project was developed with the assistance of several state-of-the-art AI models:
- GitHub Copilot
- Anthropic's Claude (Sonnet)
- OpenAI's GPT-3.5
- OpenAI's GPT-4.1
- OpenAI's GPT-5 Mini Preview

These AI models provided code suggestions, debugging assistance, and helped shape the project's architecture.

## Contact

- **Author**: VN-Hao
- **GitHub**: [VN-Hao](https://github.com/VN-Hao)
