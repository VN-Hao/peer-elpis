# Peer Elpis - AI Assistant with Voice Cloning

An AI assistant application that combines chat functionality with advanced voice cloning capabilities using OpenVoice, featuring a Live2D avatar for an interactive experience.

## ✨ Features

- 💬 **Interactive Chat Interface** - Clean PyQt5-based chat with typing animations
- 🎙️ **Advanced Voice Cloning** - Self-contained OpenVoice integration with two-stage synthesis
- 👤 **Live2D Avatar** - Animated character interface with web-based rendering
- 🔊 **Flexible TTS** - Voice customization with sample selection and engine saving
- 🤖 **AI Integration** - Google Generative AI (Gemini) for intelligent responses
- 💾 **Voice Engine Management** - Save and load processed voice engines

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/VN-Hao/peer-elpis.git
cd peer-elpis
```

### 2. Install Dependencies
```bash
# Create virtual environment
python -m venv env
.\env\Scripts\activate  # Windows
source env/bin/activate  # Linux/Mac

# Install requirements
pip install -r requirements.txt
```

### 3. Launch Chat Application
```bash
python launch_chat.py
```

### 4. (Optional) Run Full Application with Avatar
```bash
python main.py
```

## 📁 Project Structure

```
peer-elpis/
├── 📁 assets/              # UI assets and avatar files
│   ├── avatar/             # Live2D avatar files
│   └── icons/              # UI icons
├── 📁 bot/                 # AI chat logic
│   └── llm_bot.py          # Generative AI integration
├── 📁 controllers/         # Avatar animation controllers
├── 📁 services/            # Core business logic
│   ├── voice_engine_service.py  # Voice processing service
│   ├── llm_service.py      # LLM integration service
│   └── tts_service.py      # Text-to-speech service
├── 📁 ui/                  # PyQt5 user interface
│   ├── chat_window.py      # Main chat interface
│   └── enhanced_voice_setup.py  # Voice setup dialog
├── 📁 voice/               # Voice synthesis engine
│   ├── openvoice/          # Self-contained OpenVoice implementation
│   ├── tts_engine.py       # Main TTS engine
│   └── openvoice_tts.py    # OpenVoice wrapper
├── 📁 tests/               # Test files and utilities
│   ├── voice/              # Voice synthesis tests
│   ├── integration/        # Integration tests
│   └── debug/              # Debug utilities
├── 📁 checkpoints/         # Voice model checkpoints
│   ├── base_speakers/      # Base voice models
│   └── converter/          # Voice conversion models
├── 📁 saved_engines/       # Saved voice engines
├── main.py                 # Full app with avatar
├── launch_chat.py          # Chat-only launcher
└── run_tests.py           # Test runner
```

## 🎙️ Voice Features

### Two-Stage Voice Synthesis
- **Base Speaker**: High-quality generic voice (5/5 quality)
- **Voice Cloning**: Clone any voice from audio samples (3-4/5 quality)
- **OpenVoice Integration**: Self-contained, no external dependencies

### Voice Engine Management
- 💾 **Save/Load Engines**: Save processed voices for instant reuse
- 📁 **Sample Detection**: Automatically detect sample voices in assets
- 🎚️ **Quality Options**: High-quality mode with enhanced processing
- 🔄 **Auto-save**: Automatically save successful voice processing

### Supported Audio Formats
- Input: MP3, WAV, M4A, FLAC
- Processing: 24kHz, 16-bit optimization
- Output: High-quality WAV synthesis

## 🧪 Testing and Development

### Run Tests
```bash
# Run all tests
python run_tests.py

# Run specific test categories
python run_tests.py voice        # Voice synthesis tests
python run_tests.py integration  # Integration tests
python run_tests.py debug        # Debug utilities
```

### Test Categories
- **Voice Tests**: TTS engine, OpenVoice integration, quality comparison
- **Integration Tests**: End-to-end voice and chat functionality
- **Debug Utilities**: LLM testing, tokenization debugging, symbol analysis

## ⚙️ Configuration

### API Keys (Optional)
Create a `.env` file for AI integration:
```bash
GOOGLE_AI_API_KEY=your_api_key_here
```

### Voice Models
The application includes all necessary voice models. On first run, it will:
1. Set up base speaker models automatically
2. Create checkpoint directories
3. Initialize the voice processing engine

## 📝 Usage Guide

### Chat-Only Mode
```bash
python launch_chat.py
```
- Clean chat interface
- Voice synthesis integration
- No avatar overhead

### Full Application
```bash
python main.py
```
- Complete experience with Live2D avatar
- Web-based animation rendering
- Avatar expression synchronization

### Voice Setup Process
1. **Launch Application**: Either mode supports voice setup
2. **Select Voice**: Choose from sample voices or upload your own
3. **Process Voice**: Application processes audio with OpenVoice
4. **Save Engine**: Save processed voice for future use
5. **Chat with Voice**: AI responses use your selected voice

## 🛠️ Troubleshooting

### Common Issues
- **Voice not working**: Check if PyTorch/torchaudio are installed correctly
- **Chat not responding**: Verify Google AI API key in `.env` file
- **Import errors**: Ensure all dependencies from `requirements.txt` are installed
- **Audio quality issues**: Try using base speaker mode for clearest quality

### Development
- All test files are in `tests/` directory organized by functionality
- Debug utilities in `tests/debug/` help diagnose specific issues
- Use `run_tests.py` to verify functionality after changes

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[OpenVoice](https://github.com/myshell-ai/OpenVoice)** - Advanced voice cloning technology
- **Live2D** - Avatar animation framework  
- **PyQt5** - Cross-platform GUI toolkit
- **Google Generative AI** - Intelligent chat responses

---
**Author**: [VN-Hao](https://github.com/VN-Hao)
